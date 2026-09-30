-- Script em ServerScriptService: arma de raycast + munição coletável (marcadores RetroDNAItem).
local CS = game:GetService("CollectionService")
local Players = game:GetService("Players")
local StarterPack = game:GetService("StarterPack")

local tool = Instance.new("Tool")
tool.Name, tool.RequiresHandle = "Arma", true
local handle = Instance.new("Part")
handle.Name, handle.Size = "Handle", Vector3.new(0.5, 0.8, 1.5)
handle.Parent = tool
tool:SetAttribute("Ammo", 30)

tool.Activated:Connect(function()
	local char = tool.Parent
	local root = char and char:FindFirstChild("HumanoidRootPart")
	local ammo = tool:GetAttribute("Ammo")
	if not root or ammo <= 0 then return end
	tool:SetAttribute("Ammo", ammo - 1)
	local params = RaycastParams.new()
	params.FilterDescendantsInstances = { char }
	local res = workspace:Raycast(root.Position, root.CFrame.LookVector * 80, params)
	if res then
		local model = res.Instance:FindFirstAncestorOfClass("Model")
		local hum = model and model:FindFirstChildOfClass("Humanoid")
		if hum and CS:HasTag(model, "RetroDNAEnemyLive") then hum:TakeDamage(10) end
	end
end)
tool.Parent = StarterPack

local function hook(item)
	item.Touched:Connect(function(hit)
		local plr = Players:GetPlayerFromCharacter(hit.Parent)
		if not plr or not item.Parent then return end
		local t = hit.Parent:FindFirstChildOfClass("Tool") or plr.Backpack:FindFirstChildOfClass("Tool")
		if t and t:GetAttribute("Ammo") then
			t:SetAttribute("Ammo", t:GetAttribute("Ammo") + (item:GetAttribute("Amount") or 10))
			item:Destroy()
		end
	end)
end
for _, i in ipairs(CS:GetTagged("RetroDNAItem")) do hook(i) end
