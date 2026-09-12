<!--
  物品操作菜单（查看 / 使用 / 组合）
  三种模式共用同一个弹层：
    root    → 查看 / 使用 / 组合 / 取消
    combine → 与哪个物品组合？（候选 = 其它背包物品）
    use     → 用在哪儿？（候选 = 特写对象的目标 / 全景对象）
  样式沿用原版动态创建的内联写法
-->
<script setup>
import { storeToRefs } from 'pinia'
import { useGameStore } from '../store/game'

const store = useGameStore()
const { itemMenu } = storeToRefs(store)

/** 组合模式至少要有两件物品才展示入口（原版 inv.length >= 2） */
function canCombine() {
  return store.inventory.length >= 2
}
</script>

<template>
  <div v-if="itemMenu.visible" class="pop-mask" @click.self="store.closeItemMenu()">
    <div class="pop-box" :style="{ minWidth: itemMenu.mode === 'root' ? '280px' : '280px' }">
      <h3>{{ itemMenu.title }}</h3>

      <div class="pop-acts">
        <!-- 根菜单 -->
        <template v-if="itemMenu.mode === 'root'">
          <button class="act-btn" @click="store.inspectItem()">查看</button>
          <button v-if="store.scene?.mode === 'closeup' && store.scene?.object_id"
                  class="act-btn" @click="store.useItemDirect()">使用</button>
          <button v-else class="act-btn" @click="store.useItemDirect()">使用</button>
          <button v-if="canCombine()" class="act-btn" @click="store.pickTarget('combine')">组合</button>
          <button class="act-btn" style="margin-top:6px" @click="store.closeItemMenu()">取消</button>
        </template>

        <!-- 目标选择 -->
        <template v-else>
          <div v-if="!itemMenu.candidates.length" class="empty-hint">（没有可用目标）</div>
          <button v-for="c in itemMenu.candidates" :key="c.id" class="act-btn"
                  @click="store.confirmTarget(c)">
            {{ itemMenu.mode === 'use' ? '用在 ' + c.name : '与 ' + c.name + ' 组合' }}
          </button>
          <button class="act-btn" @click="store.closeItemMenu()">取消</button>
        </template>
      </div>
    </div>
  </div>
</template>
