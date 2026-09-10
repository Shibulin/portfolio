using UnityEngine;
using System.Collections;
using System.Collections.Generic;

public class UIManager : MonoBehaviour
{
    public static UIManager Instance;

    public List<GameObject> correctUIPrefabs; // 正确 UI 预制体列表
    public List<GameObject> wrongUIPrefabs;   // 错误 UI 预制体列表

    private void Awake()
    {
        // 实现单例模式
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    /// <summary>
    /// 显示正确的 UI 信息
    /// </summary>
    public void ShowCorrectUI()
    {
        if (correctUIPrefabs.Count == 0)
        {
            Debug.LogError("没有可用的正确 UI 预制体");
            return;
        }

        int randomIndex = Random.Range(0, correctUIPrefabs.Count);
        GameObject uiPrefab = correctUIPrefabs[randomIndex];
        GameObject uiInstance = Instantiate(uiPrefab, transform);
        uiInstance.SetActive(true);

        // 2秒后隐藏
        StartCoroutine(HideUIAfterDelay(uiInstance, 2f));
    }

    /// <summary>
    /// 显示错误的 UI 信息
    /// </summary>
    public void ShowWrongUI()
    {
        if (wrongUIPrefabs.Count == 0)
        {
            Debug.LogError("没有可用的错误 UI 预制体");
            return;
        }

        int randomIndex = Random.Range(0, wrongUIPrefabs.Count);
        GameObject uiPrefab = wrongUIPrefabs[randomIndex];
        GameObject uiInstance = Instantiate(uiPrefab, transform);
        uiInstance.SetActive(true);

        // 2秒后隐藏
        StartCoroutine(HideUIAfterDelay(uiInstance, 2f));
    }

    /// <summary>
    /// 延迟隐藏 UI
    /// </summary>
    private IEnumerator HideUIAfterDelay(GameObject uiObject, float delay)
    {
        yield return new WaitForSeconds(delay);
        Destroy(uiObject);
    }
}