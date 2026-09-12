<!--
  右侧边栏：背包 / 线索 双栏
  - 标签切换由 store.curTab 控制，保持原版 .side-tab.active 行为
  - 空列表时显示 empty-hint（文案与原版一致）
  - 物品点击 → 打开物品菜单（步 5 实现，当前先接入 store 已备好的入口）
-->
<script setup>
import { storeToRefs } from 'pinia'
import { useGameStore } from '../store/game'

const store = useGameStore()
const { started, curTab, inventory, clues } = storeToRefs(store)
</script>

<template>
  <div id="sidebar" v-show="started">
    <div id="sideTabs">
      <div class="side-tab" :class="{ active: curTab === 'inv' }" data-tab="inv"
           @click="curTab = 'inv'">
        🎒 背包 <span class="badge" id="invBadge">{{ inventory.length }}</span>
      </div>
      <div class="side-tab" :class="{ active: curTab === 'clue' }" data-tab="clue"
           @click="curTab = 'clue'">
        💡 线索 <span class="badge" id="clueBadge">{{ clues.length }}</span>
      </div>
    </div>
    <div id="sideBody">
      <template v-if="curTab === 'inv'">
        <div v-for="it in inventory" :key="it.id" class="inv-item" :data-id="it.id"
             @click="store.openItemMenu(it.id)">
          <span class="em">{{ it.icon }}</span><span>{{ it.name }}</span>
        </div>
        <div v-if="!inventory.length" class="empty-hint">背包是空的<br>去场景里找找可拾取的东西</div>
      </template>
      <template v-else>
        <div v-for="(c, i) in clues" :key="i" class="clue-item">{{ c }}</div>
        <div v-if="!clues.length" class="empty-hint">还没有线索<br>查看物品和场景会记录到这里</div>
      </template>
    </div>
  </div>
</template>
