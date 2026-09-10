using UnityEngine;
using UnityEngine.UI;

public class TujianManager : MonoBehaviour
{
    // 图鉴的根物体
    public GameObject tujianPanel;

    // 标记图鉴是否已显示
    private bool isTujianVisible = false;

    // 标记是否正在处理点击事件
    private bool isProcessingClick = false;

    // 动画持续时间（可选）
    public float animationDuration = 0.3f;

    // 动画插值（可选）
    private RectTransform rectTransform;
    private Vector2 hiddenPosition;
    private Vector2 visiblePosition;

    void Start()
    {
        // 获取图鉴面板的 RectTransform 组件
        if (tujianPanel != null)
        {
            rectTransform = tujianPanel.GetComponent<RectTransform>();
            if (rectTransform != null)
            {
                // 记录图鉴隐藏和显示时的位置
                hiddenPosition = rectTransform.anchoredPosition;
                visiblePosition = hiddenPosition + new Vector2(0, 1080); // 假设图鉴从屏幕底部滑入
            }
            else
            {
                Debug.LogWarning("图鉴面板缺少 RectTransform 组件");
            }
        }
        else
        {
            Debug.LogError("图鉴面板未在 Inspector 中赋值");
        }

    }

    void Update()
    {
        if (Input.GetMouseButtonUp(0))
        {
            if (!isProcessingClick && isTujianVisible)
            {
                HideTujian();
            }
        }


    }

    // 当点击图鉴按钮时调用
    public void OnTujianButtonClicked()
    {
        if (tujianPanel == null)
        {
            Debug.LogError("图鉴面板未在 Inspector 中赋值");
            return;
        }

        isProcessingClick = true;

        if (!isTujianVisible)
        {
            ShowTujian();
        }
        else
        {
            HideTujian();
        }

        // 防止点击事件立即触发
        Invoke("ResetProcessingClick", animationDuration);
    }

    // 显示图鉴
    private void ShowTujian()
    {
        if (tujianPanel != null)
        {
            // 启用图鉴面板
            tujianPanel.SetActive(true);

           

            isTujianVisible = true;
        }
    }

    // 隐藏图鉴
    private void HideTujian()
    {
        if (tujianPanel != null)
        {
            
            {
                // 禁用图鉴面板
                tujianPanel.SetActive(false);
            };

            isTujianVisible = false;
        }
    }

    // 重置点击处理状态
    private void ResetProcessingClick()
    {
        isProcessingClick = false;
    }

    
}