-- RetroDNA Observer (MesenCE): captura a tabela de sprites (OAM), o input e o scroll do PPU.
-- Requer "Allow access to I/O and OS functions" (Debugger Settings > Script Window > Restrictions).
local CONFIG = {
  out = "__OUT__",                       -- caminho ABSOLUTO do arquivo de saída
  mode = "__MODE__",                     -- "bot" (joga sozinho) ou "human" (você joga)
  seconds = __SECONDS__,                 -- segundos GRAVADOS de gameplay (0 = até parar o script)
  seed = __SEED__,
  skip_title = __SKIP__,                 -- bot: navega pelos menus apertando só Start até o gameplay
  gameplay_sprites = __GAMEPLAY_SPRITES__, -- sprites visíveis a partir dos quais a tela conta como gameplay
  menu_timeout = 120,                    -- bot: desiste se o gameplay não for detectado em N segundos
  every = 6,                             -- frames entre amostras (~10 Hz a 60 fps)
}
math.randomseed(CONFIG.seed)
local OAM = emu.memType.snesSpriteRam

local function say(msg) emu.log("RDNA: " .. msg) end

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

-- arquivo de saída (aberto uma única vez; "w" evita misturar sessões antigas)
local f, ioFailed, finished = nil, false, false
local function handle()
  if f or ioFailed then return f end
  if type(io) ~= "table" then
    ioFailed = true
    emu.displayMessage("RetroDNA ERRO", "I/O desligado: ative 'Allow access to I/O and OS functions'")
    say("ERRO: biblioteca io indisponivel (acesso a I/O desligado nas configuracoes do Mesen)")
    return nil
  end
  local file, err = io.open(CONFIG.out, "w")
  if not file then
    ioFailed = true
    emu.displayMessage("RetroDNA ERRO", "Falha I/O: " .. tostring(err))
    say("ERRO io.open: " .. tostring(err))
    return nil
  end
  f = file
  f:write(string.format('{"meta":{"source":"oam","mode":"%s","every":%d,"scroll_keys":%d}}\n',
    CONFIG.mode, CONFIG.every, #scrollKeys))
  f:flush()
  say("gravando em " .. CONFIG.out)
  return f
end
handle()

local autoMenus = CONFIG.mode == "bot" and CONFIG.skip_title
local inGame = not autoMenus      -- sem navegação de menus, considera que já está no jogo
local frame, recFrames, held, holdUntil = 0, 0, {}, 0
local DIRS = { {}, { "up" }, { "down" }, { "left" }, { "right" }, { "up", "left" }, { "up", "right" }, { "down", "left" }, { "down", "right" } }
local botInput = {
  a = false, b = false, x = false, y = false, l = false, r = false,
  up = false, down = false, left = false, right = false, select = false, start = false,
}

local function updateBotState()
  for k in pairs(botInput) do botInput[k] = false end
  if autoMenus and not inGame then
    -- MENUS (título, seleção de personagem...): só Start, em pulsos limpos, a cada 2,5 s.
    -- Nunca mexe o direcional nem aperta A/B aqui: era assim que o bot caía em "PASSWORD".
    if frame % 150 < 8 then botInput.start = true end
    return
  end
  -- GAMEPLAY: movimento aleatório e ações
  if frame >= holdUntil then
    held = DIRS[math.random(#DIRS)]
    holdUntil = frame + math.random(20, 90)
  end
  for _, d in ipairs(held) do botInput[d] = true end
  if frame % 24 < 6 then botInput.y = true end    -- ataque (varia por jogo)
  if frame % 90 < 4 then botInput.b = true end
  if frame % 150 < 4 then botInput.a = true end
end

-- o jogo lê o controle: aplica as teclas do bot neste instante.
-- Sem este callback o bot NUNCA aperta nada (e o campo "in" da telemetria fica vazio).
emu.addEventCallback(function()
  if CONFIG.mode == "bot" then
    updateBotState()
    emu.setInput(botInput, 0)
  end
end, emu.eventType.inputPolled)

local function finish()
  if finished then return end
  finished = true
  if f then f:flush() f:close() f = nil end
  if type(io) == "table" and not ioFailed then
    local d = io.open(CONFIG.out .. ".done", "w") -- avisa o Python que a sessão terminou
    if d then d:write("ok") d:close() end
  end
  say("sessao encerrada (" .. frame .. " frames, " .. recFrames .. " gravados)")
end

-- sprites visíveis na tela (mesma regra do conversor Python: y < 224 e x dentro da tela)
local function visibleSprites(raw)
  local n = 0
  for i = 0, 127 do
    local y = raw[4 * i + 2]
    local hi = raw[513 + i // 4] >> ((i % 4) * 2)
    local x = raw[4 * i + 1] - ((hi & 1) ~= 0 and 256 or 0)
    if y < 224 and x > -16 and x < 256 then n = n + 1 end
  end
  return n
end

local raw, hex = {}, {}
local hiTicks, loTicks, ticks = 0, 0, 0
emu.addEventCallback(function()
  if finished then return end
  frame = frame + 1
  if frame % CONFIG.every == 0 then
    for i = 0, 543 do raw[i + 1] = emu.read(i, OAM, false) end
    ticks = ticks + 1
    local count = visibleSprites(raw)
    if ticks % 20 == 0 then   -- a cada ~2 s: use estes números para calibrar --gameplay-sprites
      say("sprites=" .. count .. " gameplay=" .. tostring(inGame))
    end
    if autoMenus then
      if count >= CONFIG.gameplay_sprites then hiTicks, loTicks = hiTicks + 1, 0 else hiTicks, loTicks = 0, loTicks + 1 end
      if not inGame and hiTicks >= 10 then      -- 1 s seguido com muitos sprites
        inGame = true
        say("gameplay detectado (" .. count .. " sprites); comecando a gravar")
      elseif inGame and loTicks >= 60 then      -- 6 s seguidos com poucos sprites (game over, menu, pausa)
        inGame = false
        say("saiu do gameplay (" .. count .. " sprites); voltando a apertar Start")
      end
      if not inGame and recFrames == 0 and frame >= CONFIG.menu_timeout * 60 then
        say("ERRO: gameplay nao detectado em " .. CONFIG.menu_timeout .. "s; ajuste --gameplay-sprites (veja as linhas 'sprites=' acima)")
        finish()
        if emu.exit then emu.exit(1) else emu.stop(1) end
        return
      end
    end
    local file = (inGame and handle()) or nil
    if file then
      for i = 0, 543 do hex[i + 1] = string.format("%02x", raw[i + 1]) end
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
  if inGame then recFrames = recFrames + 1 end
  if inGame and CONFIG.seconds > 0 and recFrames >= CONFIG.seconds * 60 then
    finish()
    if emu.exit then emu.exit(0) else emu.stop(0) end
  end
end, emu.eventType.endFrame)

emu.addEventCallback(finish, emu.eventType.scriptEnded)
emu.displayMessage("RetroDNA", "observador iniciado (" .. CONFIG.mode .. ")")
say("observador iniciado, modo " .. CONFIG.mode .. ", gameplay a partir de " .. CONFIG.gameplay_sprites .. " sprites")
