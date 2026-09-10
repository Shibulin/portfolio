using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class MainMenu : MonoBehaviour
{
    public Button startButton;
    public Button exitButton;

    void Start()
    {
        // 为开始游戏按钮添加监听器
        startButton.onClick.AddListener(OnStartGame);

        // 为结束游戏按钮添加监听器
        exitButton.onClick.AddListener(OnExitGame);
    }

    public void OnStartGame()
    {
        SceneManager.LoadScene("SelectScenes");
    }

    // 结束游戏的方法
    public void OnExitGame()
    {
        Application.Quit();

        #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
        #endif
    }
}