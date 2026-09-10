using UnityEngine;
using UnityEngine.EventSystems;

public class DragHandler2 : MonoBehaviour, IBeginDragHandler, IDragHandler, IEndDragHandler
{
    public Transform originalParent;
    private RectTransform rectTransform;
    private Canvas canvas;
    private CraftingManager2 craftingManager2;

    void Awake()
    {
        rectTransform = GetComponent<RectTransform>();
        canvas = GetComponentInParent<Canvas>();
        craftingManager2 = FindObjectOfType<CraftingManager2>();
    }

    public void OnBeginDrag(PointerEventData eventData)
    {
        originalParent = transform.parent;
        transform.SetParent(canvas.transform);
    }

    public void OnDrag(PointerEventData eventData)
    {
        rectTransform.anchoredPosition += eventData.delta / canvas.scaleFactor;
    }

    public void OnEndDrag(PointerEventData eventData)
    {
        bool isOverSlot = false;
        foreach (Slot slot in craftingManager2.craftingSlots)
        {
            if (slot != null && slot.gameObject.activeSelf && RectTransformUtility.RectangleContainsScreenPoint(slot.GetComponent<RectTransform>(), eventData.position, canvas.worldCamera))
            {
                isOverSlot = true;
                transform.SetParent(slot.transform);
                transform.localPosition = Vector3.zero;
                slot.item = GetComponent<Item>();
                craftingManager2.AddItemToSlot(slot.index, GetComponent<Item>());
                break;
            }
        }

        if (!isOverSlot)
        {
            // 如果没有接触任何卡槽，则回到原始父对象
            transform.SetParent(originalParent);
            transform.localPosition = Vector3.zero;
        }
    }
}