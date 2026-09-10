using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// 工程静态体检：不进 Play 模式，直接打开场景读取组件字段，交叉校验配方/病人/卡牌是否对得上。
/// 菜单：Tools/Demo/导出工程体检信息
/// 也可命令行调用：Unity -batchmode -executeMethod DemoInspector.DumpBatch
/// 输出：项目根/DemoLogs/inspect.txt
/// </summary>
public static class DemoInspector
{
    static List<string> buf = new List<string>();

    static string OutPath =>
        Path.GetFullPath(Path.Combine(Application.dataPath, "..", "DemoLogs", "inspect.txt"));

    [MenuItem("Tools/Demo/导出工程体检信息")]
    public static void Dump()
    {
        buf.Clear();
        Write("=== 工程静态体检 ===");
        Write($"时间: {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
        Write("");

        CheckMainMenu();
        CheckSelect();
        CheckClinic();

        string dir = Path.GetDirectoryName(OutPath);
        Directory.CreateDirectory(dir);
        File.WriteAllText(OutPath, string.Join("\n", buf) + "\n");
        Debug.Log("[Demo] 体检完成 → " + OutPath);
    }

    public static void DumpBatch()
    {
        Dump();
    }

    static void OpenScene(string path)
    {
        var scene = EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
        Write($"--- 打开场景: {scene.name} ({path}) ---");
    }

    // ---------------- 主菜单 ----------------
    static void CheckMainMenu()
    {
        OpenScene("Assets/Scenes/MainMenuScene.unity");
        var menu = UnityEngine.Object.FindObjectOfType<MainMenu>();
        if (menu == null) { Write("[ERROR] 场景里没有 MainMenu"); return; }
        Write($"MainMenu 找到。startButton={(menu.startButton != null ? menu.startButton.name : "未绑定")}  " +
              $"exitButton={(menu.exitButton != null ? menu.exitButton.name : "未绑定")}");
        Write("");
    }

    // ---------------- 选择界面 ----------------
    static void CheckSelect()
    {
        OpenScene("Assets/Scenes/SelectScenes.unity");
        var sel = UnityEngine.Object.FindObjectOfType<SelectMenu>();
        if (sel == null) { Write("[ERROR] 场景里没有 SelectMenu"); return; }
        Write($"SelectMenu 找到。普通按钮={(sel.PutongButton != null ? sel.PutongButton.name : "未绑定")}  " +
              $"无限按钮={(sel.WuxianButton != null ? sel.WuxianButton.name : "未绑定")}");
        Write("");
    }

    // ---------------- 诊室（核心） ----------------
    static void CheckClinic()
    {
        OpenScene("Assets/Scenes/DocterScene1.unity");
        var cm = UnityEngine.Object.FindObjectOfType<CraftingManager>();
        if (cm == null) { Write("[ERROR] 场景里没有 CraftingManager"); return; }

        Write("## CraftingManager");
        Write($"槽位数 craftingSlots = {(cm.craftingSlots != null ? cm.craftingSlots.Length : 0)}");
        Write($"配方数 recipes = {(cm.recipes != null ? cm.recipes.Length : 0)}");
        Write($"产物数 recipeResult = {(cm.recipeResult != null ? cm.recipeResult.Length : 0)}");

        // 反射读私有倒计时
        var f = typeof(CraftingManager).GetField("countdownTime",
            BindingFlags.NonPublic | BindingFlags.Instance);
        Write($"倒计时 countdownTime = {(f != null ? f.GetValue(cm).ToString() : "读取失败")} 秒");
        Write("");

        // 配方表
        Write("## 配方表");
        var recipeNames = new List<string>();
        if (cm.recipeResult != null)
            foreach (var r in cm.recipeResult)
                recipeNames.Add(r != null ? r.recipeName : "<null>");

        for (int i = 0; i < (cm.recipes != null ? cm.recipes.Length : 0); i++)
        {
            string mats = cm.recipes[i];
            string prod = i < recipeNames.Count ? recipeNames[i] : "<缺产物>";
            Write($"[{i}] {prod}  ←  {mats}");
        }
        Write("");

        // 病人 prefab 需求
        Write("## 病人预制体");
        var wants = new List<string>();
        if (cm.characterPrefabs != null)
        {
            for (int i = 0; i < cm.characterPrefabs.Length; i++)
            {
                var p = cm.characterPrefabs[i];
                if (p == null) { Write($"[{i}] <空>"); continue; }
                var cs = p.GetComponent<CharacterSlot>();
                string want = cs != null ? cs.characterName : "<无 CharacterSlot>";
                wants.Add(want);
                bool ok = recipeNames.Contains(want);
                Write($"[{i}] {p.name}  需要 = {want}   {(ok ? "有配方 OK" : "!! 配方表里没有这个产物 !!")}");
            }
        }
        Write("");

        // 卡牌池
        Write("## 卡牌池（可拖的药材）");
        var pool = new HashSet<string>();
        var cgm = UnityEngine.Object.FindObjectOfType<CardGroupManager>();
        if (cgm != null && cgm.cardGroups != null)
        {
            Write($"卡组数 cardGroups = {cgm.cardGroups.Count}");
            for (int g = 0; g < cgm.cardGroups.Count; g++)
            {
                var grp = cgm.cardGroups[g];
                if (grp == null) { Write($"  组{g}: <空>"); continue; }
                var items = grp.GetComponentsInChildren<Item>(true);
                var names = new List<string>();
                foreach (var it in items)
                {
                    if (it == null) continue;
                    names.Add(it.itemName);
                    pool.Add(it.itemName);
                }
                Write($"  组{g} ({grp.name}) 共 {names.Count} 张: {string.Join("、", names)}");
            }
        }
        else
        {
            Write("[WARN] 场景里没有 CardGroupManager，改为扫描场景内全部 Item");
            foreach (var it in UnityEngine.Object.FindObjectsOfType<Item>(true))
                if (it != null) pool.Add(it.itemName);
            Write($"场景内 Item 共 {pool.Count} 种: {string.Join("、", pool)}");
        }
        Write("");

        // 交叉校验：每味材料是否在卡牌池里
        Write("## 交叉校验：配方材料 是否都在卡牌池");
        bool allOk = true;
        for (int i = 0; i < (cm.recipes != null ? cm.recipes.Length : 0); i++)
        {
            var mats = cm.recipes[i].Split(',');
            var missing = new List<string>();
            foreach (var raw in mats)
            {
                string m = raw.Trim();
                if (!pool.Contains(m)) missing.Add(m);
            }
            string prod = i < recipeNames.Count ? recipeNames[i] : "?";
            if (missing.Count > 0)
            {
                allOk = false;
                Write($"  ✗ {prod}: 缺少材料 {string.Join("、", missing)}");
            }
            else
            {
                Write($"  ✓ {prod}: 材料齐全 ({mats.Length} 味)");
            }
        }
        Write("");
        Write(allOk ? "结论：配方材料与卡牌池匹配，可以录制" : "结论：有材料缺失，录制时会自动跳过这些味，需要补卡或换配方");
    }

    static void Write(string s)
    {
        buf.Add(s);
        Debug.Log("[Demo] " + s);
    }
}
