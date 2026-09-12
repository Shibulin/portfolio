/**
 * TextRoom 全局状态（Pinia · setup 语法）
 *
 * 设计要点：
 * 1. 服务端仍是唯一数据源：每次动作返回整包 { state, scene, inventory_detail, narration }，
 *    store 只负责把它存进 data，其余全部由 computed 派生 —— 原版 render() 里
 *    那一大串手动 DOM 更新因此在 Vue 里自然消失。
 * 2. 保留原版仅有的几处"命令式副作用"：关卡切换弹衔接页、旁白入列(留最近4条)、
 *    特写反馈日志(留最近2条)、通关切结算页。
 * 3. 同步 window.lastData —— 冒烟脚本与录屏脚本依赖这个全局变量读取状态。
 */
import { defineStore } from 'pinia'
import { computed, reactive, ref } from 'vue'
import { api, cleanNarr } from '../api'
import { ROOM_NAMES } from '../constants'

export const useGameStore = defineStore('game', () => {
  /* ==================== 服务端整包数据 ==================== */
  const data = ref(null)
  const starting = ref(false)
  const started = ref(false)      // 封面是否已关闭

  /* ==================== 旁观 UI 状态 ==================== */
  const curTab = ref('inv')       // 右侧栏：inv | clue
  const narrations = ref([])      // [{ text, cls }] 保留最近 4 条

  /* ==================== 特写弹窗内的互动反馈 ==================== */
  const fbLog = ref([])           // 最近 2 条
  const fbObj = ref(null)

  /* ==================== 各类弹层 ==================== */
  const pwd = reactive({ visible: false, buf: '', len: 0, title: '输入密码', sub: '', msg: '' })
  const arrowVisible = ref(false)
  const itemMenu = reactive({ visible: false, item: null, mode: 'root', candidates: [], title: '' })
  const gate = reactive({ visible: false, level: 1, name: '' })
  const winVisible = ref(false)

  /* ==================== 内部句柄 ==================== */
  let lastRoom = null
  let narrTimer = null
  let narrTries = 0

  /* ==================== 派生状态（原版 render 的手动赋值在这里全部变成 computed） ==================== */
  const state = computed(() => data.value?.state || null)
  const scene = computed(() => data.value?.scene || null)
  const inventory = computed(() => data.value?.inventory_detail || [])
  const clues = computed(() => state.value?.clues || [])
  const isPanorama = computed(() => scene.value?.mode === 'panorama')
  const isCloseup = computed(() => scene.value?.mode === 'closeup')
  const finished = computed(() => !!state.value?.finished)
  const inventoryDetail = computed(() => data.value?.inventory_detail || [])

  const levelLabel = computed(() => {
    if (!state.value) return ''
    const room = ROOM_NAMES[state.value.room] || scene.value?.room_name || ''
    return `第 ${state.value.level} 关 · ${room}`
  })
  const progress = computed(() => state.value?.progress ?? 0)

  /* ==================== 旁白 ==================== */
  function narr(text, cls = '') {
    const msg = cleanNarr(text)
    if (!msg) return
    narrations.value.forEach(n => { if (n.cls === 'narr-new') n.cls = 'narr-old' })
    narrations.value.push({ text: msg, cls: `narr-new ${cls}`.trim() })
    if (narrations.value.length > 4) narrations.value = narrations.value.slice(-4)
  }

  /** 后台 LLM 润色轮询：最多 8 次 × 1.5s，拿到就停 */
  function pollNarrationLatest() {
    if (narrTimer) clearInterval(narrTimer)
    narrTries = 0
    narrTimer = setInterval(async () => {
      narrTries += 1
      try {
        const r = await api.narrationLatest()
        if (r && r.narration) {
          narr(r.narration)
          // 润色回来时若特写弹窗开着，同步替换反馈区最后一条
          if (isCloseup.value && fbLog.value.length) {
            fbLog.value = [...fbLog.value.slice(0, -1), cleanNarr(r.narration)]
          }
          clearInterval(narrTimer); narrTimer = null
          return
        }
      } catch (_) { /* 轮询失败静默重试 */ }
      if (narrTries >= 8) { clearInterval(narrTimer); narrTimer = null }
    }, 1500)
  }

  /* ==================== 特写反馈区 ==================== */
  /** 弹窗打开时追加一条反馈；不在弹窗中则忽略 */
  function pushFeedback(text) {
    if (!isCloseup.value || !text) return
    fbLog.value = [...fbLog.value, cleanNarr(text)].slice(-2)
  }

  /* ==================== 主渲染入口 ==================== */
  function render(payload) {
    data.value = payload
    // 冒烟 / 录屏脚本通过全局 lastData 读取状态，必须同步
    window.lastData = payload

    const st = payload.state

    // 关卡衔接：房间切换（非首次、非通关）→ 白底黑字衔接页
    if (lastRoom && st.room !== lastRoom && !st.finished) showGate(st)
    lastRoom = st.room

    // 旁白
    if (payload.narration) narr(payload.narration)

    // 通关：白底全屏结算
    if (st.finished) { showWin(payload); return }

    // 场景模式副作用
    if (payload.scene?.mode === 'panorama') {
      fbObj.value = null
      fbLog.value = []
    } else if (payload.scene?.mode === 'closeup') {
      if (fbObj.value !== payload.scene.object_id) { fbObj.value = payload.scene.object_id; fbLog.value = [] }
      if (payload.narration) fbLog.value = [...fbLog.value, cleanNarr(payload.narration)].slice(-2)
    }
  }

  /* ==================== 动作发送 ==================== */
  async function send(action, params = {}) {
    try {
      const payload = await api.action(action, params)
      render(payload)
      pollNarrationLatest()
    } catch (err) {
      const msg = err.message || String(err)
      narr('⚠️ ' + msg, 'narr-err')
      pushFeedback('⚠️ ' + msg)                  // 错误进弹窗反馈区
      if (pwd.visible) {                         // 密码弹窗开着时同步到弹窗提示
        pwd.msg = msg
        pwd.buf = ''
      }
    }
  }

  /* ==================== 开局 / 重开 ==================== */
  async function start() {
    starting.value = true
    try {
      const payload = await api.start()
      started.value = true
      render(payload)
      pollNarrationLatest()
      return true
    } catch (err) {
      narr('⚠️ 开局失败：' + (err.message || err), 'narr-err')
      return false
    } finally {
      starting.value = false
    }
  }

  async function restart() {
    winVisible.value = false
    lastRoom = null
    fbObj.value = null
    fbLog.value = []
    narrations.value = []
    try {
      const payload = await api.start()
      render(payload)
      pollNarrationLatest()
    } catch (err) {
      narr('⚠️ 重开失败：' + (err.message || err), 'narr-err')
    }
  }

  /* ==================== 密码弹窗 ==================== */
  function openPasswordModal(objectName, length) {
    pwd.buf = ''
    pwd.len = length
    pwd.title = `🔐 ${objectName} · 输入密码`
    pwd.sub = `${length} 位数字密码`
    pwd.msg = ''
    pwd.visible = true
  }
  function closePasswordModal() { pwd.visible = false }

  function padPress(k) {
    if (k === 'C') { pwd.buf = ''; pwd.msg = ''; return }
    if (k === 'OK') {
      if (pwd.buf.length < pwd.len) {
        pwd.msg = `还差 ${pwd.len - pwd.buf.length} 位`
        return
      }
      const code = pwd.buf
      const target = scene.value?.object_id
      pwd.visible = false
      send('enter_password', { target_id: target, code })
      return
    }
    if (pwd.buf.length < pwd.len) pwd.buf += k
  }

  function backspacePassword() {
    pwd.buf = pwd.buf.slice(0, -1)
    pwd.msg = ''
  }

  /* ==================== 电子屏箭头弹窗 ==================== */
  function openArrowModal() { arrowVisible.value = true }
  function closeArrowModal() { arrowVisible.value = false }
  function pressArrow(direction) {
    arrowVisible.value = false
    send('press_arrow', { direction })
  }

  /* ==================== 物品菜单（查看 / 使用 / 组合） ==================== */
  function openItemMenu(id) {
    const it = inventoryDetail.value.find(x => x.id === id)
    if (!it) return
    itemMenu.item = it
    itemMenu.mode = 'root'
    itemMenu.candidates = []
    itemMenu.title = `${it.icon} ${it.name}`
    itemMenu.visible = true
  }
  function closeItemMenu() { itemMenu.visible = false }

  /** 打开目标选择（组合 = 其它背包物品；使用 = 当前特写对象） */
  function pickTarget(mode) {
    const it = itemMenu.item
    if (!it) return
    itemMenu.mode = mode
    itemMenu.title = mode === 'combine'
      ? `与哪个物品组合？`
      : `把 ${it.icon} ${it.name} 用在哪儿？`
    itemMenu.candidates = mode === 'combine'
      ? inventoryDetail.value.filter(x => x.id !== it.id)
      : (scene.value?.mode === 'closeup' ? (scene.value?.interactive_targets || []) : (scene.value?.objects || []))
  }

  function confirmTarget(target) {
    const it = itemMenu.item
    const mode = itemMenu.mode
    itemMenu.visible = false
    if (mode === 'combine') send('combine', { item_a: it.id, item_b: target.id })
    else send('use', { item_id: it.id, target_id: target.id })
  }

  /** 使用道具：特写中直接作用于当前对象；全景中给出提示 */
  function useItemDirect() {
    const it = itemMenu.item
    const sc = scene.value
    itemMenu.visible = false
    if (sc?.mode === 'closeup' && sc.object_id) {
      send('use', { item_id: it.id, target_id: sc.object_id })
    } else {
      narr(`💡 「${it.name}」需要走到具体的东西面前才能用——先点击场景里的目标看看。`)
    }
  }

  function inspectItem() {
    const it = itemMenu.item
    itemMenu.visible = false
    send('inspect', { item_id: it.id })
  }

  /* ==================== 关卡衔接页 ==================== */
  function showGate(st) {
    gate.level = st.level
    gate.name = ROOM_NAMES[st.room] || ''
    gate.visible = true
  }
  function dismissGate() { gate.visible = false }

  /* ==================== 通关 ==================== */
  const winText = ref('')
  function showWin(payload) {
    winText.value = cleanNarr(payload.narration || '你走出卷帘门，逃出了密室！')
    winVisible.value = true
  }

  return {
    // 数据
    data, starting, started, state, scene, inventory, inventoryDetail, clues,
    isPanorama, isCloseup, finished, levelLabel, progress,
    // 旁白
    narrations, narr, pollNarrationLatest, pushFeedback,
    // 特写反馈
    fbLog, fbObj,
    // 弹层
    pwd, arrowVisible, itemMenu, gate, winVisible, winText,
    // 动作
    render, send, start, restart,
    openPasswordModal, closePasswordModal, padPress, backspacePassword,
    openArrowModal, closeArrowModal, pressArrow,
    openItemMenu, closeItemMenu, pickTarget, confirmTarget, useItemDirect, inspectItem,
    dismissGate,
    // 侧栏
    curTab,
  }
})
