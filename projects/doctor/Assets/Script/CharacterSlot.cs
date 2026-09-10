using UnityEngine;
using UnityEngine.UI;

public class CharacterSlot : MonoBehaviour
{
    public string characterName;

    public int score = 0; // 初始化积分
    public Text scoreText; // 假设你有一个 UI Text 用于显示人物积分

    void Update()
    {
        // 更新人物积分显示
        if (scoreText != null)
        {
            scoreText.text = "积分: " + score;
        }
        else
        {
            Debug.LogWarning("Score Text UI 未设置在人物上");
        }
    }
}