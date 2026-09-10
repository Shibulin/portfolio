using UnityEngine;
using UnityEngine.EventSystems;

public class DragHandler : MonoBehaviour, IBeginDragHandler, IDragHandler, IEndDragHandler
{
    public Transform originalParent;
    private RectTransform rectTransform;
    private Canvas canvas;
    private CraftingManager craftingManager;

    void Awake()
    {
        rectTransform = GetComponent<RectTransform>();
        canvas = GetComponentInParent<Canvas>();
        craftingManager = FindObjectOfType<CraftingManager>();
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
        foreach (Slot slot in craftingManager.craftingSlots)
        {
            if (slot != null && slot.gameObject.activeSelf && RectTransformUtility.RectangleContainsScreenPoint(slot.GetComponent<RectTransform>(), eventData.position, canvas.worldCamera))
            {
                isOverSlot = true;
                transform.SetParent(slot.transform);
                transform.localPosition = Vector3.zero;
                slot.item = GetComponent<Item>();
                craftingManager.AddItemToSlot(slot.index, GetComponent<Item>());
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