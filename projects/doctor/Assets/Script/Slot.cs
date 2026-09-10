using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class Slot : MonoBehaviour
{
    public Item item;
    public int index;

    // 静态列表，用于存储所有 CraftingManager 实例
    private static List<CraftingManager> craftingManagers = new List<CraftingManager>();

    // 方法用于注册 CraftingManager 实例
    public static void RegisterCraftingManager(CraftingManager manager)
    {
        if (!craftingManagers.Contains(manager))
        {
            craftingManagers.Add(manager);
        }
    }

    void OnMouseUp()
    {
        // 调用所有 CraftingManager 的 OnClickSlot 方法
        foreach (CraftingManager manager in craftingManagers)
        {
            manager.OnClickSlot(this);
        }
    }
}