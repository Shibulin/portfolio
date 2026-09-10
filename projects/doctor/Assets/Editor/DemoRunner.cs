using UnityEditor;
using UnityEngine;

/// <summary>
/// Demo 录制的编辑器入口。菜单：Tools/Demo/...
/// 运行日志输出到 项目根/DemoLogs/demo_run.log
/// </summary>
public static class DemoRunner
{
    const string KEY = "DemoPlayer.AutoRun";

    [MenuItem("Tools/Demo/▶ 运行演示流程（自动进 Play）")]
    static void Run()
    {
        EditorPrefs.SetBool(KEY, true);
        Debug.Log("[Demo] 已开启自动演示，进入 Play 模式…");
        EditorApplication.EnterPlaymode();
    }

    [MenuItem("Tools/Demo/■ 关闭自动演示（正常手动游玩）")]
    static void Off()
    {
        EditorPrefs.SetBool(KEY, false);
        Debug.Log("[Demo] 已关闭自动演示，下次 Play 不会自动跑流程");
    }

    [MenuItem("Tools/Demo/打开运行日志目录")]
    static void OpenLog()
    {
        string dir = System.IO.Path.GetFullPath(
            System.IO.Path.Combine(Application.dataPath, "..", "DemoLogs"));
        System.IO.Directory.CreateDirectory(dir);
        EditorUtility.RevealInFinder(dir);
    }
}
