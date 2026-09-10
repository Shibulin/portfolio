using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

[System.Serializable]
public class CardGroupManager : MonoBehaviour
{
    // 当前显示的卡组索引
    private int currentGroupIndex = 0;

    // 所有卡组的列表
    public List<GameObject> cardGroups;

    // 卡牌父对象，用于放置卡牌
    public Transform cardParent;

    // 左右按钮
    public Button leftButton;
    public Button rightButton;

    // 指示器文本
    public Text groupIndicator;

    // 卡牌布局组件（Grid Layout Group 或 Horizontal Layout Group）
    public LayoutGroup layoutGroup;

    void Start()
    {
        if (cardGroups == null || cardGroups.Count == 0)
        {
            Debug.LogError("没有卡组数据！");
            return;
        }

        // 初始化卡组
        DisplayGroup(currentGroupIndex);

        // 关联按钮事件
        leftButton.onClick.AddListener(SwitchLeft);
        rightButton.onClick.AddListener(SwitchRight);
    }

    // 显示指定索引的卡组
    public void DisplayGroup(int index)
    {
        // 清空当前显示的卡牌
        foreach (Transform child in cardParent)
        {
            Destroy(child.gameObject);
        }

        // 获取当前卡组
        GameObject currentGroup = cardGroups[index];

        // 实例化并显示卡牌
        Instantiate(currentGroup, cardParent);

        // 调整布局
        StartCoroutine(AdjustLayout());

        // 更新指示器
        groupIndicator.text = $"Group {index + 1} ({currentGroup.transform.childCount}/{currentGroup.transform.childCount})";
    }

    // 调整布局的协程
    private IEnumerator AdjustLayout()
    {
        // 等待一帧，让所有卡牌实例化完成
        yield return null;

        // 如果使用 Grid Layout Group
        GridLayoutGroup grid = layoutGroup as GridLayoutGroup;
        if (grid != null)
        {
            // 根据卡牌数量动态设置列数
            int columnCount = Mathf.Min(currentGroupIndex < 3 ? 6 : 4, cardParent.childCount);
            grid.constraint = GridLayoutGroup.Constraint.FixedColumnCount;
            grid.constraintCount = columnCount;
        }

        // 如果使用 Horizontal Layout Group
        HorizontalLayoutGroup horizontal = layoutGroup as HorizontalLayoutGroup;
        if (horizontal != null)
        {
            // 根据卡牌数量调整间距
            float spacing = 10f; // 默认间距
            float totalWidth = cardParent.GetComponent<RectTransform>().rect.width;
            float cardWidth = cardParent.GetChild(0).GetComponent<RectTransform>().rect.width;
            int cardCount = cardParent.childCount;
            float totalSpacing = (cardCount - 1) * spacing;
            float availableWidth = totalWidth - totalSpacing;
            float newSpacing = (availableWidth - cardCount * cardWidth) / (cardCount - 1);
            horizontal.spacing = newSpacing > 0 ? newSpacing : spacing;
        }
    }

    // 向左切换卡组
    public void SwitchLeft()
    {
        currentGroupIndex--;
        if (currentGroupIndex < 0)
        {
            currentGroupIndex = cardGroups.Count - 1; // 循环到最后一组
        }
        DisplayGroup(currentGroupIndex);
    }

    // 向右切换卡组
    public void SwitchRight()
    {
        currentGroupIndex++;
        if (currentGroupIndex >= cardGroups.Count)
        {
            currentGroupIndex = 0; // 循环到第一组
        }
        DisplayGroup(currentGroupIndex);
    }
}