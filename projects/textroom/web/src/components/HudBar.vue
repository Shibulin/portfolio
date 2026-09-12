<!-- 顶部 HUD：关卡名 + 进度条 -->
<script setup>
import { storeToRefs } from 'pinia'
import { useGameStore } from '../store/game'

const store = useGameStore()
const { started, levelLabel, progress } = storeToRefs(store)
</script>

<template>
  <div id="hud" v-show="started">
    <div class="hud-chip" id="levelName">{{ levelLabel }}</div>
    <div id="progressWrap"><div id="progressBar" :style="{ width: progress + '%' }"></div></div>
    <div class="hud-chip" id="progressTxt">{{ progress }}%</div>
  </div>
</template>
