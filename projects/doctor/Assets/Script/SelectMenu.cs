using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class SelectMenu : MonoBehaviour
{
    public Button PutongButton;
    public Button WuxianButton;

    void Start()
    {
        // 为开始游戏按钮添加监听器
        PutongButton.onClick.AddListener(OnStartPutongGame);

        // 为结束游戏按钮添加监听器
        WuxianButton.onClick.AddListener(OnStartWuxianGame);
    }

    public void OnStartPutongGame()
    {
        SceneManager.LoadScene("DocterScene1");
    }

    // 结束游戏的方法
    public void OnStartWuxianGame()
    {
        SceneManager.LoadScene("DocterScene2");

    }
}
