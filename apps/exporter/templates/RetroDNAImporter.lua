-- Plugin do Roblox Studio: importa map.json gerado pelo RetroDNA.
local HttpService = game:GetService("HttpService")
local StudioService = game:GetService("StudioService")
local CS = game:GetService("CollectionService")

local toolbar = plugin:CreateToolbar("RetroDNA")
local button = toolbar:CreateButton("Importar", "Importar map.json", "")

local function part(parent, name, size, pos, color)
	local p = Instance.new("Part")
	p.Name, p.Size, p.Position, p.Anchored = name, size, pos, true
	p.Color = Color3.fromHex(color)
	p.Parent = parent
	return p
end

local function marker(parent, tag, name, pos, color, attrs)
	local m = part(parent, name, Vector3.new(2, 2, 2), pos, color)
	m.CanCollide, m.Transparency = false, 0.5
	for k, v in pairs(attrs or {}) do m:SetAttribute(k, v) end
	CS:AddTag(m, tag)
	return m
end

local function build(data)
	local old = workspace:FindFirstChild("RetroDNAMap")
	if old then old:Destroy() end
	local root = Instance.new("Folder"); root.Name = "RetroDNAMap"
	local T = data.tile_size
	local W, H = data.room_size[1], data.room_size[2]
	local rooms = {}
	for _, r in ipairs(data.rooms) do
		rooms[r.id] = r
		local ox, oy = r.origin[1] * T, r.origin[2] * T
		local f = part(root, "Floor_" .. r.id, Vector3.new(W * T, 1, H * T),
			Vector3.new(ox + W * T / 2, -0.5, oy + H * T / 2), data.palette.floor)
		f.TopSurface = Enum.SurfaceType.Smooth
		for y, row in ipairs(r.tiles) do -- une sequências horizontais de parede em uma peça só
			local x = 1
			while x <= #row do
				if row:sub(x, x) == "#" then
					local s = x
					while x <= #row and row:sub(x, x) == "#" do x += 1 end
					local len = x - s
					part(root, "Wall", Vector3.new(len * T, 8, T),
						Vector3.new(ox + (s - 1 + len / 2) * T, 4, oy + (y - 0.5) * T), data.palette.wall)
				else
					x += 1
				end
			end
		end
	end
	local function at(e) return Vector3.new((e.x + 0.5) * T, 3, (e.y + 0.5) * T) end
	for _, e in ipairs(data.enemies) do
		marker(root, "RetroDNAEnemy", e.type, at(e), "#ff3b3b",
			{ Archetype = e.archetype, Speed = e.speed, Health = e.health, Aggro = e.aggro, DisplayName = e.type })
	end
	for _, n in ipairs(data.npcs) do marker(root, "RetroDNARescue", n.type, at(n), "#ffe14a", { DisplayName = n.type }) end
	for _, i in ipairs(data.items) do marker(root, "RetroDNAItem", i.kind, at(i), "#4ac8ff", { Amount = i.amount }) end
	local sr = rooms[data.start_room]
	local spawn = Instance.new("SpawnLocation")
	spawn.Anchored = true
	spawn.Position = Vector3.new((sr.origin[1] + W / 2) * T, 1, (sr.origin[2] + H / 2) * T)
	spawn.Parent = root
	root.Parent = workspace
end

button.Click:Connect(function()
	local file = StudioService:PromptImportFile({ "json" })
	if not file then return end
	local ok, data = pcall(function() return HttpService:JSONDecode(file:GetBinaryContents()) end)
	if not ok or data.format ~= "retrodna-map/1" then warn("RetroDNA: arquivo inválido") return end
	build(data)
end)
