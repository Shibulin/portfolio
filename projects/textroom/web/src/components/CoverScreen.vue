<!-- 开始页：白底居中，点击后关闭并进入游戏 -->
<script setup>
import { storeToRefs } from 'pinia'
import { useGameStore } from '../store/game'

const store = useGameStore()
const { starting } = storeToRefs(store)
</script>

<template>
  <div id="cover">
    <h1 class="cover-title">TEXTROOM · 密室逃脱</h1>
    <button id="cover-btn" class="cover-btn" :disabled="starting" @click="store.start()">
      {{ starting ? '加载中…' : '开始游戏' }}
    </button>
  </div>
</template>
