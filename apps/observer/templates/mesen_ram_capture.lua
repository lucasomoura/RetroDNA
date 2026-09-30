-- Captura de telemetria no Mesen 2 -> telemetry.jsonl (formato de retrodna/telemetry.py)
-- ATENÇÃO: endereços de RAM são POR JOGO. Encontre-os com o Debugger (RAM search) e preencha CONFIG.
-- Habilite em Script > Settings: acesso a I/O. Nomes da API podem variar entre versões do Mesen.
local CONFIG = {
  out = "C:/retrodna/sessao1.jsonl",           -- use caminho ABSOLUTO (crie a pasta antes); troque a cada sessão
  every = 6,                                   -- frames entre amostras (~10 Hz a 60 fps)
  player = { x = 0x0000, y = 0x0000 },         -- endereços de 16 bits (WRAM) da posição do jogador
  hp = 0x0000,                                 -- vida do jogador (queda = evento damage)
  rescue = 0x0000,                             -- contador de objetivos/resgates (aumento = evento rescue)
  item = 0x0000,                               -- contador de itens coletados (aumento = evento item)
  area = 0x0000,                               -- id da sala/área atual (opcional; habilita level design)
  enemies = { base = 0x0000, stride = 0x20, count = 8, active = 0, x = 2, y = 4 }, -- offsets na tabela de objetos
}
-- nomes de memType variam entre versões; o primeiro que existir é usado
local mem = emu.memType.snesWorkRam or emu.memType.workRam or emu.memType.snesMemory
local function r16(a) return emu.readWord(a, mem, false) end
local f = assert(io.open(CONFIG.out, "w"), "não abriu o arquivo: habilite acesso a I/O e confira a pasta")
emu.displayMessage("RetroDNA", "captura iniciada")
local frame, lastHp, lastRescue, lastItem = 0, nil, nil, nil

emu.addEventCallback(function()
  frame = frame + 1
  if frame % CONFIG.every ~= 0 then return end
  local px, py = r16(CONFIG.player.x), r16(CONFIG.player.y)
  local es = {}
  local E = CONFIG.enemies
  for i = 0, E.count - 1 do
    local b = E.base + i * E.stride
    if emu.read(b + E.active, mem, false) ~= 0 then
      es[#es + 1] = string.format('{"id":%d,"x":%d,"y":%d}', i, r16(b + E.x), r16(b + E.y))
    end
  end
  local hp, rs, it = emu.read(CONFIG.hp, mem, false), emu.read(CONFIG.rescue, mem, false), emu.read(CONFIG.item, mem, false)
  local ev = ""
  if lastHp and hp < lastHp then ev = ',"event":"damage"' end
  if lastItem and it > lastItem then ev = ',"event":"item"' end
  if lastRescue and rs > lastRescue then ev = ',"event":"rescue"' end
  lastHp, lastRescue, lastItem = hp, rs, it
  local area = CONFIG.area ~= 0 and string.format(',"area":"%d"', emu.read(CONFIG.area, mem, false)) or ""
  f:write(string.format('{"t":%.2f,"px":%d,"py":%d%s,"enemies":[%s]%s}\n',
    frame / 60, px, py, area, table.concat(es, ","), ev))
  f:flush()
end, emu.eventType.endFrame)
