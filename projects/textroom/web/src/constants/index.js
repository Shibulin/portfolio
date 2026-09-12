/**
 * 场景常量表
 * HOTSPOTS 是按 AI 全景图实际物体位置标定的百分比坐标（与后端 scene_map.json 的 object id 对应）
 */

export const HOTSPOTS = {
  study: {
    door:          { x: 5,  y: 55 },
    bookshelf:     { x: 19, y: 55 },
    safe:          { x: 32, y: 62 },
    desk:          { x: 44, y: 64 },
    clock:         { x: 57, y: 38 },
    picture_frame: { x: 68, y: 36 },
  },
  living_room: {
    main_gate:    { x: 4,  y: 47 },
    fish_tank:    { x: 12, y: 61 },
    fridge:       { x: 25, y: 53 },
    wall_clock:   { x: 28, y: 22 },
    sofa:         { x: 41, y: 59 },
    coffee_table: { x: 44, y: 65 },
    tv_cabinet:   { x: 58, y: 65 },
    garage_door:  { x: 73, y: 55 },
  },
  garage: {
    exit_door:  { x: 19, y: 37 },
    remote:     { x: 13, y: 68 },
    keypad:     { x: 39, y: 40 },
    car:        { x: 57, y: 54 },
    tool_board: { x: 64, y: 23 },
    tool_box:   { x: 71, y: 68 },
  },
}

/** 热点图标（按对象 ID） */
export const EMOJI = {
  bookshelf: '📚', desk: '🗄', picture_frame: '🖼', clock: '🕰', safe: '🔐', door: '🚪',
  main_gate: '🚪', garage_door: '🛗', coffee_table: '🫖', fridge: '🧊',
  wall_clock: '🕰', tv_cabinet: '📺', sofa: '🛋', fish_tank: '🐟',
  exit_door: '🚪', keypad: '⌨️', remote: '📻', car: '🚗', tool_board: '🔨', tool_box: '🧰',
}

export const ROOM_NAMES = { study: '书房', living_room: '客厅', garage: '车库' }

/** 密码键盘键位布局 */
export const PAD_KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'C', '0', 'OK']
