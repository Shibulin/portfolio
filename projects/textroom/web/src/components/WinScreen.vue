<!--
  通关结算页：白底全屏
  ⚠️ #win-bg 的 CSS 写死了 display:none，必须用 :class="{show: ...}"
-->
<script setup>
import { storeToRefs } from 'pinia'
import { useGameStore } from '../store/game'

const store = useGameStore()
const { winVisible, winText } = storeToRefs(store)
</script>

<template>
  <div id="win-bg" :class="{ show: winVisible }">
    <div class="win-inner">
      <h2>🏆 通关！</h2>
      <p id="win-text">{{ winText }}</p>
      <button id="win-restart" @click="store.restart()">再玩一次</button>
    </div>
  </div>
</template>
