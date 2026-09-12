<!--
  场景层：全屏底图 + 热点按钮
  - 底图仅房间切换时换 src（对应原版 bg.dataset.room 判断），避免同关重复拉图
  - 热点坐标取自常量表 HOTSPOTS，缺省落在画面正中
  - 热点仅在「全景模式」出现；特写模式下原版会隐藏整个 #modalMask，
    底图本身不动，所以这里不卸载 #scene，仅按模式控制热点
-->
<script setup>
import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useGameStore } from '../store/game'
import { EMOJI, HOTSPOTS } from '../constants'

const store = useGameStore()
const { started, scene, isPanorama } = storeToRefs(store)

/** 当前底图地址（仅房间切换时更新，复刻原版数据集判断） */
const bgSrc = ref('')
watch(() => scene.value?.room_id, (room) => {
  if (room && scene.value?.image) bgSrc.value = scene.value.image
}, { immediate: true })

/** 全景热点：坐标查表，带图标前缀 */
const hotspots = computed(() => {
  if (!isPanorama.value) return []
  const coords = HOTSPOTS[scene.value.room_id] || {}
  return (scene.value.objects || []).map((o) => {
    const c = coords[o.id] || { x: 50, y: 50 }
    const em = EMOJI[o.id] ? EMOJI[o.id] + ' ' : ''
    return { id: o.id, name: o.name, text: `${em}${o.name}`, x: c.x, y: c.y }
  })
})
</script>

<template>
  <div id="scene" v-show="started">
    <img id="bg" :src="bgSrc" alt="scene">
    <div id="hotspotHolder">
      <button
        v-for="h in hotspots"
        :key="h.id"
        class="hotspot"
        :data-id="h.id"
        :style="{ left: h.x + '%', top: h.y + '%' }"
        @click="store.send('look', { object_id: h.id })"
      >{{ h.text }}</button>
    </div>
  </div>
</template>
