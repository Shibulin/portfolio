using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;

public class DraggableItem : MonoBehaviour, IBeginDragHandler, IDragHandler, IEndDragHandler
{
    private Transform originalParent;
    private CanvasGroup canvasGroup;
    private CraftingManager craftingManager;

    void Awake()
    {
        canvasGroup = GetComponent<CanvasGroup>();
        if (canvasGroup == null)
        {
            canvasGroup = gameObject.AddComponent<CanvasGroup>();
        }
        craftingManager = FindObjectOfType<CraftingManager>();
    }

    public void OnBeginDrag(PointerEventData eventData)
    {
        originalParent = transform.parent;
        transform.SetParent(transform.parent.parent); // 将其设置为 resultSlot 的父对象
        canvasGroup.blocksRaycasts = false;
        Debug.Log("开始拖拽: " + gameObject.name);
    }

    public void OnDrag(PointerEventData eventData)
    {
        transform.position = eventData.position;
        Debug.Log("拖拽中: " + gameObject.name);
    }

    public void OnEndDrag(PointerEventData eventData)
    {
        bool isOverCharacterSlot = false;
        bool isCorrect = false; // 初始化 isCorrect 变量

        // 获取当前鼠标位置下的所有碰撞体
        Collider2D[] colliders = Physics2D.OverlapPointAll(eventData.position);

        foreach (Collider2D collider in colliders)
        {
            if (collider.CompareTag("CharacterSlot"))
            {
                isOverCharacterSlot = true;

                // 获取 CharacterSlot 组件
                CharacterSlot characterSlot = collider.GetComponent<CharacterSlot>();
                if (characterSlot != null)
                {
                    // 获取人物名称
                    string characterName = characterSlot.characterName;

                    // 获取当前药方卡牌的 Item 组件
                    Item item = gameObject.GetComponent<Item>();
                    if (item != null)
                    {
                        // 检查配方是否正确
                        Debug.Log("检测配方: " + item.recipeName + " 与人物: " + characterName);

                        // 调用 IsCorrectRecipe 方法并赋值给 isCorrect
                        isCorrect = craftingManager.IsCorrectRecipe(item, characterName);

                        // 销毁人物预制体
                        DestroyCharacter(collider.gameObject);

                        // 销毁药方卡牌
                        Destroy(gameObject);
                        Debug.Log("销毁药方卡牌: " + gameObject.name);

                        // 生成新人物
                        this.craftingManager.SpawnNewCharacter(collider.transform.position);

                        // 根据结果修改积分
                        if (isCorrect)
                        {
                            craftingManager.ModifyScore(10);
                            Debug.Log("配方正确，增加 10 分。当前积分: " + craftingManager.Score);
                        }
                        else
                        {
                            craftingManager.ModifyScore(-5);
                            Debug.Log("配方错误，扣除 5 分。当前积分: " + craftingManager.Score);
                            // 仅在无限模式下调用 OnWrongRecipe
                            if (craftingManager.currentGameMode == CraftingManager.GameMode.InfiniteMode)
                            {
                                craftingManager.OnWrongRecipe();
                            }
                        }

                        // 显示 UI 信息
                        if (craftingManager.uiManager != null)
                        {
                            if (isCorrect)
                            {
                                craftingManager.uiManager.ShowCorrectUI();
                            }
                            else
                            {
                                craftingManager.uiManager.ShowWrongUI();
                            }
                        }
                        else
                        {
                            Debug.LogWarning("UIManager 未在 CraftingManager 中设置");
                        }

                        break; // 找到后跳出循环
                    }
                    else
                    {
                        Debug.LogError("DraggableItem 物体上没有找到 Item 组件");
                    }
                }
                else
                {
                    Debug.LogError("CharacterSlot 物体上没有找到 CharacterSlot 组件");
                }
            }
        }

        if (!isOverCharacterSlot)
        {
            // 如果没有与任何 CharacterSlot 碰撞，返回原来的父对象
            transform.SetParent(originalParent);
            transform.localPosition = Vector3.zero;
            Debug.Log("返回原始父对象: " + originalParent.name);
        }

        canvasGroup.blocksRaycasts = true;
    }

    void DestroyCharacter(GameObject character)
    {
        // 销毁人物预制体
        Destroy(character);
        Debug.Log("销毁人物: " + character.name);
    }
}