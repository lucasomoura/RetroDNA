-- RetroDNA Observer: captura OAM + input + scroll
local CONFIG = {
  out = "__OUT__",          -- caminho ABSOLUTO do arquivo de saída
  mode = "__MODE__",        -- "bot" ou "human"
  seconds = __SECONDS__,    -- duração da sessão
  seed = __SEED__,
  skip_title = __SKIP__,    -- ignora tela inicial
  every = 6,                -- amostragem a cada 6 frames
}
math.randomseed(CONFIG.seed)
local OAM = emu.memType.snesSpriteRam

local f = nil
local function getFileHandle()
  if not f then
    local file, err = io.open(CONFIG.out, "a")
    if not file then
      emu.displayMessage("RetroDNA ERRO", "Falha I/O: " .. tostring(err))
      return nil
    end
    f = file
  end
  return f
end

-- Grava cabeçalho
local fileInit = getFileHandle()
if fileInit then
  fileInit:write(string.format('{"meta":{"source":"oam","mode":"%s","every":%d}}\n', CONFIG.mode, CONFIG.every))
  fileInit:flush()
end

local frame, held, holdUntil = 0, {}, 0
local DIRS = { {}, { "up" }, { "down" }, { "left" }, { "right" }, { "up", "left" }, { "up", "right" }, { "down", "left" }, { "down", "right" } }

-- Estrutura fixa de botões do P1
local botInput = {
  a = false, b = false, x = false, y = false,
  l = false, r = false,
  up = false, down = false, left = false, right = false,
  select = false, start = false
}

local function updateBotState()
  if frame >= holdUntil then
    held = DIRS[math.random(#DIRS)]
    holdUntil = frame + math.random(20, 90)
  end

  -- Limpa estado dos botões
  for k in pairs(botInput) do
    botInput[k] = false
  end

  -- Aplica direcionais sorteados
  for _, d in ipairs(held) do
    botInput[d] = true
  end

  -- Pressiona botões de ação periodicamente
  if frame % 24 < 6 then botInput.y = true end
  if frame % 90 < 4 then botInput.b = true end
  if frame % 150 < 4 then botInput.a = true end

  -- Pula telas de título/menu nos primeiros segundos
  if CONFIG.skip_title and frame < 1200 and frame % 60 < 20 then
    botInput.start = true
    botInput.a = true
  end
end

-- Callback invocado no exato momento em que o jogo lê as portas do controlador
emu.addEventCallback(function()
  if CONFIG.mode == "bot" then
    updateBotState()
    emu.setInput(botInput, 0)
  end
end, emu.eventType.inputPolled)

local hex = {}
emu.addEventCallback(function()
  frame = frame + 1

  if frame % CONFIG.every == 0 then
    for i = 0, 543 do hex[i + 1] = string.format("%02x", emu.read(i, OAM, false)) end
    
    local cur = (CONFIG.mode == "bot") and botInput or (emu.getInput(0) or {})
    local pressed = {}
    for k, v in pairs(cur) do 
      if v == true then pressed[#pressed + 1] = k end 
    end
    table.sort(pressed)

    local file = getFileHandle()
    if file then
      file:write(string.format('{"f":%d,"in":"%s","oam":"%s"}\n', frame, table.concat(pressed, ","), table.concat(hex)))
      file:flush()
    end
  end

  if CONFIG.seconds > 0 and frame >= CONFIG.seconds * 60 then
    if f then
      f:flush()
      f:close()
      f = nil
    end
    if emu.exit then emu.exit(0) else emu.stop(0) end
  end
end, emu.eventType.endFrame)

emu.addEventCallback(function()
  if f then
    f:flush()
    f:close()
    f = nil
  end
end, emu.eventType.exit)

emu.displayMessage("RetroDNA", "Modo Bot Ativo em: " .. CONFIG.out)