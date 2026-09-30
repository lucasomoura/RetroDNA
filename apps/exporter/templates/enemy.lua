-- Script em ServerScriptService: transforma marcadores RetroDNAEnemy em inimigos ativos.
local CS = game:GetService("CollectionService")
local Players = game:GetService("Players")

local EnemySpawner = {}

function EnemySpawner:Spawn(marker)
	local model = Instance.new("Model")
	model.Name = marker:GetAttribute("DisplayName") or "Enemy"
	local root = Instance.new("Part")
	root.Name, root.Size, root.Color = "HumanoidRootPart", Vector3.new(2, 5, 2), marker.Color
	root.Position = marker.Position + Vector3.new(0, 3, 0)
	root.Parent = model
	local hum = Instance.new("Humanoid")
	hum.MaxHealth = marker:GetAttribute("Health") or 30
	hum.Health = hum.MaxHealth
	hum.WalkSpeed = marker:GetAttribute("Speed") or 8
	hum.Parent = model
	model.PrimaryPart = root
	CS:AddTag(model, "RetroDNAEnemyLive")
	model.Parent = workspace
	marker.Transparency = 1

	local aggro = marker:GetAttribute("Aggro") or 50
	local lastHit = 0
	root.Touched:Connect(function(hit)
		local h = hit.Parent and hit.Parent:FindFirstChildOfClass("Humanoid")
		if h and Players:GetPlayerFromCharacter(hit.Parent) and os.clock() - lastHit > 1 then
			lastHit = os.clock()
			h:TakeDamage(10)
		end
	end)
	task.spawn(function()
		while hum.Health > 0 and model.Parent do
			local target, best
			for _, p in ipairs(Players:GetPlayers()) do
				local r = p.Character and p.Character:FindFirstChild("HumanoidRootPart")
				if r then
					local d = (r.Position - root.Position).Magnitude
					if not best or d < best then target, best = r, d end
				end
			end
			if target and best < aggro then hum:MoveTo(target.Position) end
			task.wait(0.25)
		end
		task.wait(1)
		model:Destroy()
	end)
end

for _, m in ipairs(CS:GetTagged("RetroDNAEnemy")) do EnemySpawner:Spawn(m) end
CS:GetInstanceAddedSignal("RetroDNAEnemy"):Connect(function(m) EnemySpawner:Spawn(m) end)
