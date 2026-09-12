<!--
  TextRoom 根组件
  11 个组件全部就位；容器顺序对齐原版 body 的顶层结构。
-->
<script setup>
import { storeToRefs } from 'pinia'
import { useGameStore } from './store/game'
import CoverScreen from './components/CoverScreen.vue'
import SceneView from './components/SceneView.vue'
import HudBar from './components/HudBar.vue'
import SidePanel from './components/SidePanel.vue'
import NarrationBox from './components/NarrationBox.vue'
import CloseupModal from './components/CloseupModal.vue'
import PasswordPad from './components/PasswordPad.vue'
import ArrowModal from './components/ArrowModal.vue'
import ItemMenu from './components/ItemMenu.vue'
import LevelGate from './components/LevelGate.vue'
import WinScreen from './components/WinScreen.vue'

const store = useGameStore()
const { started } = storeToRefs(store)
</script>

<template>
  <!-- 开始页：开局后移除（对应原版 cover.style.display='none'） -->
  <CoverScreen v-if="!started" />

  <SceneView />
  <HudBar />
  <SidePanel />
  <NarrationBox />

  <CloseupModal />
  <PasswordPad />
  <ItemMenu />
  <ArrowModal />
  <WinScreen />
  <LevelGate />
</template>
