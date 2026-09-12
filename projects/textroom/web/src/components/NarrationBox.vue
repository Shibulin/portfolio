<!-- 底部旁白框：保留最近 4 条，新的高亮、上一条变暗 -->
<script setup>
import { nextTick, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useGameStore } from '../store/game'

const store = useGameStore()
const { started, narrations } = storeToRefs(store)

const box = ref(null)

// 原版每次 narr() 后会把滚动条拉到底，行为保持一致
watch(() => narrations.value.length, async () => {
  await nextTick()
  if (box.value) box.value.scrollTop = box.value.scrollHeight
})
</script>

<template>
  <div id="narration" ref="box" v-show="started">
    <div v-for="(n, i) in narrations" :key="i" :class="n.cls">{{ n.text }}</div>
  </div>
</template>
