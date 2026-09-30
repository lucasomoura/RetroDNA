-- RetroDNA Observer: captura SEM endereços de RAM (lê a tabela de sprites OAM + input + scroll).
-- Uso automático: `python -m retrodna auto jogo.sfc --mesen <caminho do Mesen>` (gera uma cópia configurada deste arquivo).
-- Uso manual: edite CONFIG, carregue no Script Window do Mesen, jogue, e passe o .jsonl ao `retrodna pipeline`.
local CONFIG = {
  out = "__OUT__",          -- caminho ABSOLUTO do arquivo de saída
  mode = "__MODE__",        -- "bot" (joga sozinho) ou "human" (você joga)
  seconds = __SECONDS__,    -- duração da sessão (segundos de jogo); 0 = até você parar
  seed = __SEED__,
  skip_title = __SKIP__,    -- bot: tenta passar da tela de título com Start/A nos primeiros segundos
  every = 6,                -- frames entre amostras (~10 Hz a 60 fps)
}
math.randomseed(CONFIG.seed)
local OAM = emu.memType.snesSpriteRam
local f = assert(io.open(CONFIG.out, "w"), "não abriu o arquivo de saída (habilite acesso a I/O e confira a pasta)")

-- botões existentes no controle (não presume nomes)
local base = emu.getInput(0) or {}
local has = {}
for k, _ in pairs(base) do has[k] = true end
if next(has) == nil then -- getInput pode omitir botões soltos: usa os nomes padrão do SNES
  for _, k in ipairs({ "a", "b", "x", "y", "l", "r", "up", "down", "left", "right", "select", "start" }) do has[k] = true end
end

-- chaves de scroll do PPU (câmera), descobertas em tempo de execução
local scrollKeys = {}
local okState, st = pcall(emu.getState)
if okState and type(st) == "table" then
  for k, v in pairs(st) do
    local lk = string.lower(k)
    if string.find(lk, "scroll", 1, true) and not string.find(lk, "latch", 1, true) and type(v) == "number" then
      scrollKeys[#scrollKeys + 1] = k
    end
  end
  table.sort(scrollKeys)
end
f:write(string.format('{"meta":{"source":"oam","mode":"%s","every":%d,"scroll_keys":%d}}\n', CONFIG.mode, CONFIG.every, #scrollKeys))

local frame, held, holdUntil, lastInp = 0, {}, 0, {}
local DIRS = { {}, { "up" }, { "down" }, { "left" }, { "right" }, { "up", "left" }, { "up", "right" }, { "down", "left" }, { "down", "right" } }

emu.addEventCallback(function()
  if CONFIG.mode ~= "bot" then return end
  if frame >= holdUntil then
    held = DIRS[math.random(#DIRS)]
    holdUntil = frame + math.random(20, 90)
  end
  local inp = {}
  for k, _ in pairs(has) do inp[k] = false end
  for _, d in ipairs(held) do if has[d] then inp[d] = true end end
  if has.y and frame % 24 < 6 then inp.y = true end                 -- ataque (varia por jogo)
  if has.b and frame % 90 < 4 then inp.b = true end
  if has.a and frame % 150 < 4 then inp.a = true end
  if CONFIG.skip_title and frame < 900 and frame % 120 == 30 then
    if has.start then inp.start = true end
    if has.a then inp.a = true end
  end
  lastInp = inp
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)

local hex = {}
emu.addEventCallback(function()
  frame = frame + 1
  if frame % CONFIG.every == 0 then
    for i = 0, 543 do hex[i + 1] = string.format("%02x", emu.read(i, OAM, false)) end
    local cur = (CONFIG.mode == "bot") and lastInp or (emu.getInput(0) or {})
    local pressed = {}
    for k, v in pairs(cur) do if v == true then pressed[#pressed + 1] = k end end
    table.sort(pressed)
    local sc = ""
    if #scrollKeys > 0 then
      local s2 = emu.getState()
      local parts = {}
      for _, k in ipairs(scrollKeys) do parts[#parts + 1] = string.format('"%s":%d', k, s2[k] or 0) end
      sc = ',"sc":{' .. table.concat(parts, ",") .. "}"
    end
    f:write(string.format('{"f":%d,"in":"%s","oam":"%s"%s}\n', frame, table.concat(pressed, ","), table.concat(hex), sc))
    f:flush()
  end
  if CONFIG.seconds > 0 and frame >= CONFIG.seconds * 60 then
    f:close()
    if emu.exit then emu.exit(0) else emu.stop(0) end
  end
end, emu.eventType.endFrame)
emu.displayMessage("RetroDNA", "observador iniciado (" .. CONFIG.mode .. ")")
