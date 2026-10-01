-- Mesen simulado: mesma API que o observador usa; recusa eventType inexistente como o Mesen real faria
local cbs = { inputPolled = {}, endFrame = {}, scriptEnded = {} }
local stopped, logs, applied = false, {}, {}
local starts, moves = {}, 0
FRAME = 0
emu = {
  memType = { snesSpriteRam = 1 },
  eventType = { inputPolled = "inputPolled", endFrame = "endFrame", scriptEnded = "scriptEnded", startFrame = "startFrame" },
  log = function(m) logs[#logs + 1] = m end,
  displayMessage = function(c, m) logs[#logs + 1] = "[" .. c .. "] " .. m end,
  read = function(a, t, s) if t ~= 1 then error("memType invalido") end return (a % 4 == 1) and 60 or 0 end,
  getInput = function(p) return {} end,
  setInput = function(i, p)
    applied[#applied + 1] = i
    if i.start then starts[#starts + 1] = FRAME end
    if i.up or i.down or i.left or i.right then moves = moves + 1 end
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
for _, l in ipairs(logs) do print(l) end
