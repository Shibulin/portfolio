<!--
  电子屏上下箭头弹窗
  只有 ⬆ / ⬇ 两个按钮，效果由服务端按门态分流：
    门未开：⬆ 升起卷帘门 / ⬇ 没有动静
    门已开：⬆ 没有动静 / ⬇ 落下卷帘门
  样式沿用原版动态创建的内联写法（原版就是内联，未走 CSS 类）
-->
<script setup>
import { storeToRefs } from 'pinia'
import { useGameStore } from '../store/game'

const store = useGameStore()
const { arrowVisible } = storeToRefs(store)
</script>

<template>
  <div v-if="arrowVisible" class="pop-mask" @click.self="store.closeArrowModal()">
    <div class="pop-box" style="padding:22px;min-width:260px;text-align:center">
      <h3 style="margin:0 0 16px;font-size:16px">⬆⬇ 电子屏 · 玻璃面板已弹开</h3>
      <button class="act-btn primary"
              style="display:block;width:100%;margin:8px 0;padding:16px 0;font-size:26px"
              @click="store.pressArrow('up')">⬆</button>
      <button class="act-btn"
              style="display:block;width:100%;margin:8px 0;padding:16px 0;font-size:26px"
              @click="store.pressArrow('down')">⬇</button>
    </div>
  </div>
</template>
