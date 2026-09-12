<!--
  密码输入弹窗：按键键盘 + 物理键盘
  ⚠️ #pwdMask 的 CSS 写死了 display:none，必须用 :class="{show: ...}"
  物理键盘在原版是 document 级监听，这里改为按需挂载 / 卸载，避免常驻监听
-->
<script setup>
import { onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useGameStore } from '../store/game'
import { PAD_KEYS } from '../constants'

const store = useGameStore()
const { pwd } = storeToRefs(store)

/** 数字 / Backspace / Enter / Esc —— 与原版 keydown 行为一致 */
function onKey(e) {
  if (!pwd.value.visible) return
  if (/^[0-9]$/.test(e.key)) store.padPress(e.key)
  else if (e.key === 'Backspace') store.backspacePassword()
  else if (e.key === 'Enter') store.padPress('OK')
  else if (e.key === 'Escape') store.closePasswordModal()
}

onMounted(() => document.addEventListener('keydown', onKey))
onUnmounted(() => document.removeEventListener('keydown', onKey))

function keyClass(k) {
  return k === 'OK' ? 'ok' : k === 'C' ? 'cancel' : ''
}
</script>

<template>
  <div id="pwdMask" :class="{ show: pwd.visible }" @click.self="store.closePasswordModal()">
    <div id="pwdBox">
      <h3 id="pwdTitle">{{ pwd.title }}</h3>
      <div class="sub" id="pwdSub">{{ pwd.sub }}</div>
      <div id="pwdDots">
        <div v-for="i in pwd.len" :key="i" class="pwd-dot">{{ pwd.buf[i - 1] || '' }}</div>
      </div>
      <div id="pwdPad">
        <button v-for="k in PAD_KEYS" :key="k" class="pad-key" :class="keyClass(k)"
                :data-k="k" @click="store.padPress(k)">{{ k }}</button>
      </div>
      <div id="pwdMsg">{{ pwd.msg }}</div>
    </div>
  </div>
</template>
