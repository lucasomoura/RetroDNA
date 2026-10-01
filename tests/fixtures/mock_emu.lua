-- Mesen simulado: mesma API que o observador usa; recusa eventType inexistente como o Mesen real faria
local cbs = { inputPolled = {}, endFrame = {}, scriptEnded = {} }
local stopped, logs, applied = false, {}, {}
local starts, moves, firstMove = {}, 0, nil
FRAME = 0
-- MENU_RANGES="0-900,1500-2100": nesses frames a tela tem poucos sprites (menu); fora deles, muitos (gameplay)
local menus = {}
for a, b in string.gmatch(os.getenv("MENU_RANGES") or "", "(%d+)-(%d+)") do menus[#menus + 1] = { tonumber(a), tonumber(b) } end
local function inMenu()
  for _, r in ipairs(menus) do if FRAME >= r[1] and FRAME < r[2] then return true end end
  return false
end
-- CHECK="1300-1500": conta Starts e movimentos dentro dessa janela de frames
local cA, cB = string.match(os.getenv("CHECK") or "", "(%d+)-(%d+)")
cA, cB = tonumber(cA), tonumber(cB)
local checkStarts, checkMoves = 0, 0
emu = {
  memType = { snesSpriteRam = 1 },
  eventType = { inputPolled = "inputPolled", endFrame = "endFrame", scriptEnded = "scriptEnded", startFrame = "startFrame" },
  log = function(m) logs[#logs + 1] = m end,
  displayMessage = function(c, m) logs[#logs + 1] = "[" .. c .. "] " .. m end,
  read = function(a, t, s)
    if t ~= 1 then error("memType invalido") end
    if a >= 512 then return 0 end
    if a % 4 == 1 then return (inMenu() and a // 4 >= 3) and 240 or 60 end -- byte y do sprite
    return 0
  end,
  getInput = function(p) return {} end,
  setInput = function(i, p)
    applied[#applied + 1] = i
    local moving = i.up or i.down or i.left or i.right
    if i.start then starts[#starts + 1] = FRAME end
    if moving then moves = moves + 1 end
    if moving and not firstMove then firstMove = FRAME end
    if cA and FRAME >= cA and FRAME < cB then
      if i.start then checkStarts = checkStarts + 1 end
      if moving then checkMoves = checkMoves + 1 end
    end
  end,
  getState = function() return { ["snes.ppu.layers[0].hScroll"] = 12, ["snes.ppu.layers[0].vScroll"] = 3, ["snes.ppu.layers[0].hScrollLatch"] = 9 } end,
  stop = function(c) stopped = true end,
  addEventCallback = function(fn, ev)
    if ev == nil or not cbs[ev] then error("evento invalido: " .. tostring(ev)) end
    table.insert(cbs[ev], fn)
  end,
}
if os.getenv("NO_IO") == "1" then io = nil end
dofile(arg[1])
local n = 0
while not stopped and n < 100000 do
  n = n + 1
  FRAME = n
  for _, fn in ipairs(cbs.inputPolled) do fn() end
  for _, fn in ipairs(cbs.endFrame) do fn() end
end
for _, fn in ipairs(cbs.scriptEnded) do fn() end
print("frames=" .. n .. " setInput=" .. #applied .. " logs=" .. #logs)
print("start_frames=" .. (#starts > 0 and (starts[1] .. "," .. starts[#starts]) or "none") .. " moves=" .. moves)
print("first_move=" .. tostring(firstMove) .. " check_starts=" .. checkStarts .. " check_moves=" .. checkMoves)
for _, l in ipairs(logs) do print(l) end
