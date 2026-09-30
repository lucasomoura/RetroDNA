-- Script em ServerScriptService: resgate de NPCs (marcadores RetroDNARescue).
local CS = game:GetService("CollectionService")
local Players = game:GetService("Players")

local function stats(plr)
	local ls = plr:FindFirstChild("leaderstats")
	if not ls then
		ls = Instance.new("Folder"); ls.Name = "leaderstats"; ls.Parent = plr
		local v = Instance.new("IntValue"); v.Name = "Resgatados"; v.Parent = ls
	end
	return ls.Resgatados
end
Players.PlayerAdded:Connect(stats)

local total = #CS:GetTagged("RetroDNARescue")
local saved = 0
for _, npc in ipairs(CS:GetTagged("RetroDNARescue")) do
	npc.Transparency = 0
	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText, prompt.ObjectText = "Resgatar", npc:GetAttribute("DisplayName") or "NPC"
	prompt.Parent = npc
	prompt.Triggered:Connect(function(plr)
		stats(plr).Value += 1
		saved += 1
		npc:Destroy()
		if saved >= total then print("RetroDNA: todos resgatados! Vá até a sala de saída.") end
	end)
end
