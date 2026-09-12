<!--
  关卡衔接页：白底黑字，点击任意位置进入下一关
  ⚠️ #levelGate 的 CSS 写死了 display:none，必须用 :class="{show: ...}"
-->
<script setup>
import { storeToRefs } from 'pinia'
import { useGameStore } from '../store/game'

const store = useGameStore()
const { gate } = storeToRefs(store)
</script>

<template>
  <div id="levelGate" :class="{ show: gate.visible }" @click="store.dismissGate()">
    <div class="gate-level" id="gateLevel">第 {{ gate.level }} 关</div>
    <div class="gate-name" id="gateName">{{ gate.name }}</div>
    <div class="gate-hint">—— 点击任意位置继续 ——</div>
  </div>
</template>
