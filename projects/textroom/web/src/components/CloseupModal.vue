<!--
  特写弹窗：场景对象的近景 + 说明 + 互动反馈 + 动作按钮
  对应原版 renderCloseup()，含 7 个条件分支：
    1. 物品行（拾取 / 查看）
    2. 互动按钮（普通 interact）
    3. 电子屏 keypad → 打开箭头弹窗
    4. 卷帘门 exit_door → 走出通关
    5. 刻度盘 needs_dial → 向左 / 向右
    6. 密码 needs_password（已打开的不会下发该字段）
    7. 需要物品解锁 needs_item_for_unlock → 信息行

  ⚠️ 布局硬约束：
  - #modalMask 的 CSS 写死了 display:none，必须用 :class="{show: ...}"，不能用 v-if / v-show
  - 信息行必须用 <div class="act-btn">（原版即 div，改 button 会命中 :disabled 变暗）
-->
<script setup>
import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useGameStore } from '../store/game'
import { cleanNarr } from '../api'

const store = useGameStore()
const { isCloseup, scene, fbLog } = storeToRefs(store)

/** 图片仅在地址变化时更新，复用浏览器缓存（对应原版 pic.dataset.img 判断） */
const picSrc = ref('')
watch(() => scene.value?.image, (src) => { if (src) picSrc.value = src })

const title = computed(() => scene.value?.object_name || '—')
const desc = computed(() => cleanNarr(scene.value?.prereq_hint || ''))

/** 该对象身上的物品：pickable=false → 查看；否则 → 拾取 */
const items = computed(() => scene.value?.items || [])

/** 卷帘门（走出通关）与电子屏（箭头弹窗）两种特殊互动 */
const isExitDoor = computed(() => scene.value?.object_id === 'exit_door')
const isKeypad = computed(() => scene.value?.object_id === 'keypad')
</script>

<template>
  <div id="modalMask" :class="{ show: isCloseup }" @click.self="store.send('back')">
    <div id="closeup">
      <div id="closeupHead">
        <h3 id="closeupTitle">{{ title }}</h3>
        <button id="closeupClose" @click="store.send('back')">↩ 返回</button>
      </div>
      <div id="closeupBody">
        <div id="closeupImg"><img id="closeupPic" :src="picSrc" alt="closeup"></div>
        <div id="closeupBottom">
          <div id="closeupDesc">{{ desc }}</div>

          <!-- v-if 挂在元素本身：无内容时整段不渲染，保证 CSS :empty 生效 -->
          <div v-if="fbLog.length" id="closeupFeedback">
            <div v-for="(t, i) in fbLog" :key="i"
                 class="fb-line" :class="{ 'fb-new': i === fbLog.length - 1 }">{{ t }}</div>
          </div>

          <div id="closeupActs">
            <!-- 1. 对象身上的物品 -->
            <button v-for="it in items" :key="it.id"
                    class="act-btn" :class="{ primary: it.pickable !== false }"
                    @click="it.pickable === false
                      ? store.send('examine', { object_id: scene.object_id, item_id: it.id })
                      : store.send('pick_up', { object_id: scene.object_id, item_id: it.id })">
              {{ it.pickable === false ? '查看 ' + it.name : '拾取 ' + it.name }}
            </button>

            <!-- 2-4. 互动按钮 -->
            <button v-if="scene.needs_interaction" class="act-btn primary"
                    @click="isKeypad
                      ? store.openArrowModal()
                      : (isExitDoor
                        ? store.send('walk_out', {})
                        : store.send('interact', { object_id: scene.object_id }))">
              {{ scene.needs_interaction }}
            </button>

            <!-- 5. 刻度盘 -->
            <template v-if="scene.needs_dial">
              <div class="act-btn" style="flex:1 1 100%">
                旋转刻度盘 · 当前停在：{{ scene.needs_dial.position }}
              </div>
              <div style="display:flex;gap:10px;flex:1 1 100%">
                <button class="act-btn"
                        @click="store.send('turn_dial', { object_id: scene.object_id, direction: 'left' })">向左旋转</button>
                <button class="act-btn"
                        @click="store.send('turn_dial', { object_id: scene.object_id, direction: 'right' })">向右旋转</button>
              </div>
            </template>

            <!-- 6. 密码输入 -->
            <button v-if="scene.needs_password" class="act-btn primary"
                    @click="store.openPasswordModal(scene.object_name, scene.needs_password.length)">
              输入密码（{{ scene.needs_password.length }} 位）
            </button>

            <!-- 7. 需要物品解锁 -->
            <div v-if="scene.needs_item_for_unlock" class="act-btn">
              {{ scene.prereq_hint || '需要特定物品' }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
