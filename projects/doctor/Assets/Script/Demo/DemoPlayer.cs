using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;

/// <summary>
/// 演示流程自动播放器（仅录制 demo 用，不影响正常玩法）。
/// 开启方式：Unity 菜单 Tools/Demo/▶ 运行演示流程（自动进 Play）
/// 运行日志：项目根目录 DemoLogs/demo_run.log
/// </summary>
public class DemoPlayer : MonoBehaviour
{
    const string PREF_KEY = "DemoPlayer.AutoRun";
    const int SEED = 2026;

    static string LogPath =>
        Path.Combine(Application.dataPath, "..", "DemoLogs", "demo_run.log");

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
#if UNITY_EDITOR
        if (!UnityEditor.EditorPrefs.GetBool(PREF_KEY, false)) return;
        if (FindObjectOfType<DemoPlayer>() != null) return;
        var go = new GameObject("[DemoPlayer]");
        go.AddComponent<DemoPlayer>();
#endif
    }

    void Start()
    {
        Application.logMessageReceived += OnUnityLog;
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(LogPath));
            File.WriteAllText(LogPath, $"=== Demo 运行日志 {DateTime.Now:yyyy-MM-dd HH:mm:ss} ===\n");
        }
        catch (Exception e) { Debug.LogWarning("[Demo] 日志初始化失败: " + e.Message); }

        StartCoroutine(Run());
    }

    IEnumerator Run()
    {
        UnityEngine.Random.InitState(SEED);
        Log($"Demo 开始  seed={SEED}  当前场景={SceneManager.GetActiveScene().name}");

        // ---- 镜 1-2：主菜单 → 选择界面 ----
        yield return Wait(1.5f);
        var menu = FindObjectOfType<MainMenu>();
        if (menu == null) { Log("[ERROR] 未找到 MainMenu，流程中止"); yield break; }
        Log("点击「开始游戏」");
        menu.startButton.onClick.Invoke();
        yield return WaitForScene("SelectScenes", 10f);
        yield return Wait(1.5f);

        // ---- 镜 3-4：选择界面 → 诊室 ----
        var sel = FindObjectOfType<SelectMenu>();
        if (sel == null) { Log("[ERROR] 未找到 SelectMenu，流程中止"); yield break; }
        Log("点击「普通模式」");
        sel.PutongButton.onClick.Invoke();
        yield return WaitForScene("DocterScene1", 10f);
        yield return Wait(1.0f);

        var cm = FindObjectOfType<CraftingManager>();
        if (cm == null) { Log("[ERROR] 未找到 CraftingManager，流程中止"); yield break; }
        Log($"已进入诊室  槽位数={cm.craftingSlots.Length}  配方数={cm.recipes.Length}  " +
            $"结果产物数={(cm.recipeResult != null ? cm.recipeResult.Length : 0)}");

        yield return WaitFor(() => CountPatients(cm) > 0, 10f, "等待病人生成");
        Log($"场上病人数 = {CountPatients(cm)}");

        // ---- 镜 5-6：自动配药一次 ----
        yield return AutoCure(cm, 0);

        Log("=== Demo 流程结束（MVP 验证范围：镜 1-6）===");
        yield return Wait(2f);

#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#endif
    }

    // ---------------- 核心：读病人需求 → 反查配方 → 拖卡 → 合成 ----------------

    IEnumerator AutoCure(CraftingManager cm, int patientIdx)
    {
        if (cm.characterSlots == null || patientIdx >= cm.characterSlots.Length)
        {
            Log($"[ERROR] characterSlots 越界 (idx={patientIdx})");
            yield break;
        }

        var cs = cm.characterSlots[patientIdx].GetComponentInChildren<CharacterSlot>();
        if (cs == null)
        {
            Log($"[ERROR] 病人位 {patientIdx} 上没有 CharacterSlot");
            yield break;
        }

        string want = cs.characterName;
        Log($"病人[{patientIdx}] 需要：{want}");

        int idx = -1;
        if (cm.recipeResult != null)
        {
            for (int i = 0; i < cm.recipeResult.Length; i++)
            {
                var r = cm.recipeResult[i];
                if (r != null && r.recipeName == want) { idx = i; break; }
            }
        }
        if (idx < 0)
        {
            Log($"[ERROR] recipeResult 里找不到名为 {want} 的产物（检查配方表配置）");
            yield break;
        }

        string[] mats = cm.recipes[idx].Split(',');
        Log($"配方解析：{string.Join(" + ", mats)}   (recipes[{idx}] = \"{cm.recipes[idx]}\")");

        foreach (var raw in mats)
        {
            string name = raw.Trim();
            GameObject card = null;
            yield return FindCardCo(name, g => card = g);

            if (card == null)
            {
                Log($"[WARN] 场上找不到药材卡「{name}」，跳过");
                continue;
            }

            var slot = NextFreeSlot(cm);
            if (slot == null) { Log("[ERROR] 没有空槽位了"); yield break; }

            Log($"  拖「{name}」→ 槽 {slot.index}");
            yield return DragCardToSlot(card, slot);
            yield return Wait(0.35f);
        }

        cm.Craft();
        Log("执行 Craft()");
        yield return Wait(1.5f);

        string result = (cm.resultSlot != null && cm.resultSlot.item != null)
            ? cm.resultSlot.item.itemName : "空";
        Log($"合成结果槽 = {result}   目标 = {want}   {(result == want ? "✅ 匹配" : "❌ 不匹配")}");
    }

    // ---------------- 交互模拟 ----------------

    /// <summary>用 EventSystem 事件驱动真实拖拽（保留拖拽动画，落位判定靠 eventData.position）</summary>
    IEnumerator DragCardToSlot(GameObject card, Slot slot)
    {
        var es = EventSystem.current;
        if (es == null) { Log("[ERROR] 场景里没有 EventSystem"); yield break; }

        var canvas = card.GetComponentInParent<Canvas>();
        var ped = new PointerEventData(es);

        Vector2 from = RectTransformUtility.WorldToScreenPoint(
            canvas != null ? canvas.worldCamera : null, card.transform.position);
        Vector2 to = RectTransformUtility.WorldToScreenPoint(
            canvas != null ? canvas.worldCamera : null, slot.transform.position);

        ped.position = from;
        ExecuteEvents.Execute(card, ped, ExecuteEvents.beginDragHandler);
        yield return null;

        int steps = 14;
        Vector2 prev = from;
        for (int i = 1; i <= steps; i++)
        {
            Vector2 cur = Vector2.Lerp(from, to, i / (float)steps);
            ped.delta = cur - prev;
            ped.position = cur;
            ExecuteEvents.Execute(card, ped, ExecuteEvents.dragHandler);
            prev = cur;
            yield return null;
        }

        ped.position = to;
        ExecuteEvents.Execute(card, ped, ExecuteEvents.endDragHandler);
        yield return null;
    }

    int CountPatients(CraftingManager cm)
    {
        int n = 0;
        if (cm.characterSlots == null) return 0;
        foreach (var t in cm.characterSlots)
            if (t != null && t.childCount > 0) n++;
        return n;
    }

    Slot NextFreeSlot(CraftingManager cm)
    {
        foreach (var s in cm.craftingSlots)
            if (s != null && s.gameObject.activeSelf && s.item == null) return s;
        return null;
    }

    GameObject FindActiveCard(string name)
    {
        var items = FindObjectsOfType<Item>(true);
        foreach (var it in items)
        {
            if (it == null) continue;
            if (it.itemName != name) continue;
            if (!it.gameObject.activeInHierarchy) continue;
            if (it.GetComponent<DragHandler>() == null) continue;
            return it.gameObject;
        }
        return null;
    }

    /// <summary>先在当前可见卡里找，找不到就翻卡组</summary>
    IEnumerator FindCardCo(string name, Action<GameObject> cb)
    {
        var found = FindActiveCard(name);
        if (found != null) { cb(found); yield break; }

        var cgm = FindObjectOfType<CardGroupManager>();
        if (cgm != null && cgm.cardGroups != null)
        {
            for (int g = 0; g < cgm.cardGroups.Count; g++)
            {
                cgm.DisplayGroup(g);
                yield return null;
                found = FindActiveCard(name);
                if (found != null)
                {
                    Log($"  翻到第 {g + 1} 组找到「{name}」");
                    cb(found);
                    yield break;
                }
            }
        }
        cb(null);
    }

    // ---------------- 等待工具（一律用条件等待，不写死秒数） ----------------

    IEnumerator Wait(float sec) { yield return new WaitForSeconds(sec); }

    IEnumerator WaitFor(Func<bool> cond, float timeout, string desc)
    {
        float t = 0f;
        while (!cond() && t < timeout) { t += Time.deltaTime; yield return null; }
        Log($"等待[{desc}] {(cond() ? "成功" : "超时")}  用时 {t:F1}s");
    }

    IEnumerator WaitForScene(string name, float timeout)
    {
        float t = 0f;
        while (SceneManager.GetActiveScene().name != name && t < timeout)
        {
            t += Time.deltaTime;
            yield return null;
        }
        string cur = SceneManager.GetActiveScene().name;
        Log($"切换场景 → {cur}（期望 {name}）{(cur == name ? "OK" : "失败")}  用时 {t:F1}s");
    }

    // ---------------- 日志 ----------------

    void OnUnityLog(string condition, string stackTrace, LogType type)
    {
        if (type == LogType.Error || type == LogType.Exception)
            Log($"[Unity {type}] {condition}");
    }

    static void Log(string msg)
    {
        string line = $"[{DateTime.Now:HH:mm:ss}] {msg}";
        Debug.Log("[Demo] " + msg);
        try { File.AppendAllText(LogPath, line + "\n"); } catch { }
    }
}
