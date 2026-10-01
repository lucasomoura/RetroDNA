-- RetroDNA Observer (MesenCE): captura a tabela de sprites (OAM), o input e o scroll do PPU.
local CONFIG = {
  out = "__OUT__",        -- caminho ABSOLUTO do arquivo de saída
  mode = "__MODE__",      -- "bot" (joga sozinho) ou "human" (você joga)
  seconds = __SECONDS__,  -- duração da sessão em segundos
  seed = __SEED__,
  skip_title = __SKIP__,  -- bot: pula tela de título e seleção
  every = 6,              -- frames entre amostras
}
math.randomseed(CONFIG.seed)
local OAM = emu.memType.snesSpriteRam

local function say(msg) emu.log("RDNA: " .. msg) end

-- Chaves de scroll do PPU
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

-- Abertura e inicialização do Arquivo de Saída
local f, ioFailed, finished = nil, false, false
local function handle()
  if f or ioFailed then return f end
  if type(io) ~= "table" then
    ioFailed = true
    emu.displayMessage("RetroDNA ERRO", "I/O desligado no Mesen")
    return nil
  end
  local file, err = io.open(CONFIG.out, "w")
  if not file then
    ioFailed = true
    emu.displayMessage("RetroDNA ERRO", "Falha I/O: " .. tostring(err))
    return nil
  end
  f = file
  f:write(string.format('{"meta":{"source":"oam","mode":"%s","every":%d,"scroll_keys":%d}}\n', CONFIG.mode, CONFIG.every, #scrollKeys))
  f:flush()
  say("gravando em " .. CONFIG.out)
  return f
end
handle()

local frame, held, holdUntil = 0, {}, 0
local DIRS = { {}, { "up" }, { "down" }, { "left" }, { "right" }, { "up", "left" }, { "up", "right" }, { "down", "left" }, { "down", "right" } }
local botInput = {
  a = false, b = false, x = false, y = false, l = false, r = false,
  up = false, down = false, left = false, right = false, select = false, start = false,
}

-- Controle de transição da tela de título e seleção
local startPhase = 0        -- 0: aguardando 1º START | 1: aguardando 2º START | 2: gameplay
local startCoolDown = 0

local function updateBotState()
  for k in pairs(botInput) do botInput[k] = false end

  if CONFIG.skip_title and startPhase < 2 then
    -- Fase 0: Dispara o 1º START para passar da tela de título (após os logos iniciais)
    if startPhase == 0 then
      if frame >= 240 and frame % 60 < 10 then -- tenta a cada 1s a partir do frame 240 (~4s)
        botInput.start = true
        startPhase = 1
        startCoolDown = frame + 180 -- Trava obrigatoriamente por ~3 segundos (180 frames)
      end
      return
    end

    -- Fase 1: Aguarda os ~3 segundos para a tela de seleção carregar e envia o 2º START
    if startPhase == 1 then
      if frame >= startCoolDown then
        if frame < startCoolDown + 15 then
          botInput.start = true -- Mantém o START pressionado por 15 frames para garantir o registro
        else
          startPhase = 2 -- Confirmação enviada! Transiciona para o Gameplay
          holdUntil = frame + 120 -- Aguarda 2s adicionais para o Level 1 carregar antes de andar
        end
      end
      return
    end
  end

  -- Fase 2: GAMEPLAY ATIVO (Controle total de movimento e ações)
  if frame >= holdUntil then
    held = DIRS[math.random(#DIRS)]
    holdUntil = frame + math.random(20, 90)
  end

  -- Aplica os direcionais sorteados
  for _, d in ipairs(held) do botInput[d] = true end

  -- Ações de botões
  if frame % 24 < 6 then botInput.y = true end    -- Ataque / Arma
  if frame % 90 < 4 then botInput.b = true end    -- Pulo / Item
  if frame % 150 < 4 then botInput.a = true end   -- Especial
end

local function finish()
  if finished then return end
  finished = true
  if f then f:flush() f:close() f = nil end
  if type(io) == "table" and not ioFailed then
    local d = io.open(CONFIG.out .. ".done", "w")
    if d then d:write("ok") d:close() end
  end
  say("sessao encerrada (" .. frame .. " frames)")
end

local hex = {}
emu.addEventCallback(function()
  if finished then return end
  frame = frame + 1
  if frame % CONFIG.every == 0 then
    local file = handle()
    if file then
      for i = 0, 543 do hex[i + 1] = string.format("%02x", emu.read(i, OAM, false)) end
      local cur = (CONFIG.mode == "bot") and botInput or (emu.getInput(0) or {})
      local pressed = {}
      for k, v in pairs(cur) do if v == true then pressed[#pressed + 1] = k end end
      table.sort(pressed)
      local sc = ""
      if #scrollKeys > 0 then
        local s2 = emu.getState()
        local parts = {}
        for _, k in ipairs(scrollKeys) do parts[#parts + 1] = string.format('"%s":%d', k, math.floor(s2[k] or 0)) end
        sc = ',"sc":{' .. table.concat(parts, ",") .. "}"
      end
      file:write(string.format('{"f":%d,"in":"%s","oam":"%s"%s}\n', frame, table.concat(pressed, ","), table.concat(hex), sc))
      file:flush()
    end
  end
  if CONFIG.seconds > 0 and frame >= CONFIG.seconds * 60 then
    finish()
    if emu.exit then emu.exit(0) else emu.stop(0) end
  end
end, emu.eventType.endFrame)

emu.addEventCallback(finish, emu.eventType.scriptEnded)
emu.displayMessage("RetroDNA", "observador iniciado (" .. CONFIG.mode .. ")")
say("observador iniciado, modo " .. CONFIG.mode)