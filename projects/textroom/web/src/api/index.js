/**
 * 后端接口封装（与原版原生 JS 的 call/send 行为完全一致）
 *
 * 接口契约：
 *   POST /api/start              -> { narration, state, scene, llm_calls }
 *   GET  /api/state              -> { state, scene, inventory_detail, llm_calls }
 *   POST /api/action {action,params} -> { narration, state, scene, inventory_detail, llm_calls }
 *   GET  /api/narration/latest   -> { narration, llm_calls }   （后台 LLM 润色结果，取走即清空）
 */

async function request(path, method = 'GET', body = null) {
  const res = await fetch(path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : null,
  })
  if (!res.ok) {
    let msg = res.statusText
    try {
      msg = (await res.json()).detail || msg
    } catch (_) { /* 响应非 JSON 时保留 statusText */ }
    throw new Error(msg)
  }
  return res.json()
}

export const api = {
  start: () => request('/api/start', 'POST', {}),
  state: () => request('/api/state'),
  action: (action, params = {}) => request('/api/action', 'POST', { action, params }),
  narrationLatest: () => request('/api/narration/latest'),
}

/** 清理 LLM 润色文本里的 Markdown 残留（**加粗**、行首 #、反引号） */
export function cleanNarr(text) {
  return (text || '').replace(/\*\*/g, '').replace(/^#+\s*/gm, '').replace(/`/g, '')
}
