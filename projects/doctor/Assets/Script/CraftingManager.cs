using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using UnityEngine.UI;
using UnityEngine.TextCore.Text;
using static UnityEditor.Progress;
using System.Linq;

public class CraftingManager : MonoBehaviour
{
    private Item currentItem;
    public Image customCursor;

    public Slot[] craftingSlots;

    public List<Item> itemsList;
    public string[] recipes;
    public Item[] recipeResult;
    public Slot resultSlot;

    public Button craftButton;

    public Transform[] characterSlots; // 人物image的Transform数组
    public GameObject[] characterPrefabs; // 所有可用的预制体

    private GameObject patient1; // 引用 Patient1 对象
    private GameObject patient2; // 引用 Patient2 对象
    private int characterCount = 0; // 计数器，确保新生成的人物数量不超过2个

    // 新增积分变量
    private int score = 0;
    public Text scoreText; // 假设你有一个 UI Text 用于显示积分

    // 新增倒计时变量
    private float countdownTime = 170f; // 2 分 50 秒 = 170 秒
    public Text countdownText; // 用于显示倒计时的 UI Text
    private bool isGameOver = false;

    // 新增 UIManager 引用
    public UIManager uiManager;

    // 新增弹出窗口变量
    public GameObject gameOverPopup;
    public Text finalScoreText; // 用于显示最终积分的 Text

    // 新增按钮引用
    public Button restartButton;
    public Button mainMenuButton;

    // 新增游戏模式枚举
    public enum GameMode
    {
        TimedMode,
        InfiniteMode
    }

    public GameMode currentGameMode;


    // 新增错误次数变量
    private int wrongRecipeCount = 0;
    public int maxWrongRecipes = 3;

    public Text remainingWrongAttemptsText; // 用于显示剩余错误次数的UI Text
    private int remainingWrongAttempts; // 剩余的错误次数
    public int Score
    {
        get { return score; }
    }

    private void Start()
    {
        // 注册自身到 Slot
        Slot.RegisterCraftingManager(this);
        // 添加按钮事件监听器
        craftButton.onClick.AddListener(Craft);
        itemsList = new List<Item>();
        foreach (Slot slot in craftingSlots)
        {
            itemsList.Add(null);
        }

        // 初始化人物预制体列表
        if (characterPrefabs.Length == 0)
        {
            Debug.LogError("没有可用的预制体");
        }

        // 找到 Patient1 和 Patient2 对象
        patient1 = GameObject.Find("Patient1");
        patient2 = GameObject.Find("Patient2");

        if (patient1 == null)
        {
            Debug.LogError("未找到名为 'Patient1' 的物体");
        }

        if (patient2 == null)
        {
            Debug.LogError("未找到名为 'Patient2' 的物体");
        }

        // 根据场景名称设置游戏模式
        string currentSceneName = UnityEngine.SceneManagement.SceneManager.GetActiveScene().name;
        if (currentSceneName == "DocterScene1")
        {
            currentGameMode = GameMode.TimedMode;
        }
        else
        {
            currentGameMode = GameMode.InfiniteMode;
            remainingWrongAttempts = maxWrongRecipes;
            UpdateRemainingWrongAttemptsUI();
        }

        // 随机生成两个初始人物，并分别设置为 Patient1 和 Patient2 的子物体
        for (int i = 0; i < 2; i++)
        {
            SpawnNewCharacter();
        }

        // 启动一个协程，定期检查并重新生成人物
        StartCoroutine(CheckAndRespawnCharacters());

        // 初始化积分显示
        UpdateScoreUI();

        // 初始化倒计时显示（仅在限时模式下）
        if (currentGameMode == GameMode.TimedMode)
        {
            UpdateCountdownUI();
            StartCoroutine(CountdownCoroutine());
        }

        // 获取 UIManager 实例
        if (uiManager == null)
        {
            uiManager = UIManager.Instance;
            if (uiManager == null)
            {
                Debug.LogError("UIManager 未在场景中找到");
            }
        }

        // 查找按钮
        if (gameOverPopup != null)
        {
            restartButton = gameOverPopup.transform.Find("RestartButton").GetComponent<Button>();
            mainMenuButton = gameOverPopup.transform.Find("MainMenuButton").GetComponent<Button>();

            if (restartButton == null)
            {
                Debug.LogWarning("未找到 Restart Button");
            }

            if (mainMenuButton == null)
            {
                Debug.LogWarning("未找到 Main Menu Button");
            }
        }
        else
        {
            Debug.LogWarning("Game Over Popup 未在 Inspector 中赋值");
        }
    }

    // 新增方法：更新积分显示
    public void UpdateScoreUI()
    {
        if (scoreText != null)
        {
            scoreText.text = "积分: " + score;
        }
        else
        {
            Debug.LogWarning("Score Text UI 未设置");
        }
    }

    // 新增方法：更新倒计时显示
    public void UpdateCountdownUI()
    {
        if (currentGameMode == GameMode.TimedMode && countdownText != null)
        {
            int minutes = Mathf.FloorToInt(countdownTime / 60);
            int seconds = Mathf.FloorToInt(countdownTime % 60);
            countdownText.text = string.Format("{0:0}:{1:00}", minutes, seconds);
        }
    }

    public void UpdateRemainingWrongAttemptsUI()
    {
        if (remainingWrongAttemptsText != null)
        {
            remainingWrongAttemptsText.text = "剩余错误次数: " + remainingWrongAttempts;
        }
        else
        {
            Debug.LogWarning("Remaining Wrong Attempts Text UI 未设置");
        }
    }

    private void Update()
    {
        if (Input.GetMouseButtonUp(0))
        {
            if (currentItem != null)
            {
                customCursor.gameObject.SetActive(false);
                Slot nearestSlot = GetNearestSlot(Input.mousePosition);
                if (nearestSlot != null)
                {
                    nearestSlot.gameObject.SetActive(true);
                    nearestSlot.GetComponent<Image>().sprite = currentItem.GetComponent<Image>().sprite;
                    nearestSlot.item = currentItem;
                    itemsList[nearestSlot.index] = currentItem;

                    currentItem = null;

                    CheckForCreatedRecipes();
                }
            }
        }
    }

    public Slot GetNearestSlot(Vector2 position)
    {
        Slot nearestSlot = null;
        float shortestDistance = float.MaxValue;

        foreach (Slot slot in craftingSlots)
        {
            float dist = Vector2.Distance(position, slot.transform.position);

            if (dist < shortestDistance)
            {
                shortestDistance = dist;
                nearestSlot = slot;
            }
        }

        return nearestSlot;
    }

    void CheckForCreatedRecipes()
    {
        // 清空resultSlot的子对象
        foreach (Transform child in resultSlot.transform)
        {
            Destroy(child.gameObject);
        }

        // 使用 Dictionary 来统计每个药材的数量
        Dictionary<string, int> currentRecipeDict = new Dictionary<string, int>();
        foreach (Item item in itemsList)
        {
            if (item != null)
            {
                if (currentRecipeDict.ContainsKey(item.itemName))
                {
                    currentRecipeDict[item.itemName]++;
                }
                else
                {
                    currentRecipeDict[item.itemName] = 1;
                }
            }
        }

        // 遍历所有配方，查找匹配
        foreach (string recipe in recipes)
        {
            // 将配方字符串分割为药材名称
            string[] recipeItems = recipe.Split(',');

            // 使用 Dictionary 来统计配方中每个药材的数量
            Dictionary<string, int> recipeDict = new Dictionary<string, int>();
            foreach (string itemName in recipeItems)
            {
                if (recipeDict.ContainsKey(itemName))
                {
                    recipeDict[itemName]++;
                }
                else
                {
                    recipeDict[itemName] = 1;
                }
            }

            bool isMatch = true;
            // 检查当前配方是否包含所有药材，并且数量匹配
            foreach (var kvp in recipeDict)
            {
                if (!currentRecipeDict.ContainsKey(kvp.Key) || currentRecipeDict[kvp.Key] < kvp.Value)
                {
                    isMatch = false;
                    break;
                }
            }

            if (isMatch)
            {
                // 实例化药方卡牌作为resultSlot的子对象
                string recipeName = recipeResult[System.Array.IndexOf(recipes, recipe)].recipeName;
                GameObject recipeObject = Instantiate(recipeResult[System.Array.IndexOf(recipes, recipe)].gameObject, resultSlot.transform);
                recipeObject.transform.localPosition = Vector3.zero;
                recipeObject.GetComponent<Image>().sprite = recipeResult[System.Array.IndexOf(recipes, recipe)].GetComponent<Image>().sprite;
                recipeObject.GetComponent<Item>().isRecipe = true;
                recipeObject.GetComponent<Item>().recipeName = recipeName;
                // 设置药方卡牌的可拖拽属性
                recipeObject.GetComponent<DraggableItem>().enabled = true;
                Debug.Log("生成配方卡牌: " + recipeName);
                break;
            }
        }
    }

    public void AddItemToSlot(int index, Item item)
    {
        itemsList[index] = item;
    }

    public void OnClickSlot(Slot slot)
    {
        if (itemsList[slot.index] != null)
        {
            itemsList[slot.index] = null;
            Destroy(slot.transform.GetChild(0).gameObject); // 销毁卡牌物体
            slot.item = null; // 移除卡牌
            CheckForCreatedRecipes();
            Debug.Log("从槽位移除物品: " + slot.index);
        }
    }

    public void OnMouseDownItem(Item item)
    {
        if (currentItem == null)
        {
            currentItem = item;
            customCursor.gameObject.SetActive(true);
            customCursor.sprite = currentItem.GetComponent<Image>().sprite;
            Debug.Log("当前选中的物品: " + item.itemName);
        }
    }

    public void Craft()
    {
        // 检查是否有匹配的配方
        // 使用 Dictionary 来统计当前配方
        Dictionary<string, int> currentRecipeDict = new Dictionary<string, int>();
        foreach (Item item in itemsList)
        {
            if (item != null)
            {
                if (currentRecipeDict.ContainsKey(item.itemName))
                {
                    currentRecipeDict[item.itemName]++;
                }
                else
                {
                    currentRecipeDict[item.itemName] = 1;
                }
            }
        }

        Debug.Log("当前配方字典: " + string.Join(", ", currentRecipeDict.Select(kvp => kvp.Key + ":" + kvp.Value)));

        // 遍历所有配方，查找匹配
        foreach (string recipe in recipes)
        {
            // 将配方字符串分割为药材名称
            string[] recipeItems = recipe.Split(',');

            // 使用 Dictionary 来统计配方中每个药材的数量
            Dictionary<string, int> recipeDict = new Dictionary<string, int>();
            foreach (string itemName in recipeItems)
            {
                if (recipeDict.ContainsKey(itemName))
                {
                    recipeDict[itemName]++;
                }
                else
                {
                    recipeDict[itemName] = 1;
                }
            }

            bool isMatch = true;
            // 检查当前配方是否包含所有药材，并且数量匹配
            foreach (var kvp in recipeDict)
            {
                if (!currentRecipeDict.ContainsKey(kvp.Key) || currentRecipeDict[kvp.Key] < kvp.Value)
                {
                    isMatch = false;
                    break;
                }
            }

            if (isMatch)
            {
                // 实例化药方卡牌作为resultSlot的子对象
                string recipeName = recipeResult[System.Array.IndexOf(recipes, recipe)].recipeName;
                GameObject recipeObject = Instantiate(recipeResult[System.Array.IndexOf(recipes, recipe)].gameObject, resultSlot.transform);
                recipeObject.transform.localPosition = Vector3.zero;
                recipeObject.GetComponent<Image>().sprite = recipeResult[System.Array.IndexOf(recipes, recipe)].GetComponent<Image>().sprite;
                recipeObject.GetComponent<Item>().isRecipe = true;
                recipeObject.GetComponent<Item>().recipeName = recipeName;
                // 设置药方卡牌的可拖拽属性
                recipeObject.GetComponent<DraggableItem>().enabled = true;
                Debug.Log("生成配方卡牌: " + recipeName);

                // 清空卡槽
                foreach (Slot slot in craftingSlots)
                {
                    if (slot.item != null)
                    {
                        itemsList[slot.index] = null;
                        Destroy(slot.transform.GetChild(0).gameObject); // 销毁卡牌物体
                        slot.item = null; // 移除卡牌
                        Debug.Log("清空槽位: " + slot.index);
                    }
                }

         

                break;
            }
        }
    }

    public bool IsCorrectRecipe(Item recipe, string characterName)
    {
        // 直接比较 recipe.recipeName 和 characterName
        Debug.Log("检查配方: " + recipe.recipeName + " 与人物: " + characterName);
        return recipe.recipeName.Equals(characterName, System.StringComparison.OrdinalIgnoreCase);
    }

    // 获取当前人物数量
    public int GetCurrentCharacterCount()
    {
        return characterSlots.Length;
    }

    // 修改 SpawnNewCharacter 方法以传递当前积分
    public void SpawnNewCharacter(Vector3 position = default)
    {
        if (characterPrefabs.Length == 0)
        {
            Debug.LogError("没有可用的预制体");
            return;
        }

        int randomIndex = Random.Range(0, characterPrefabs.Length);
        GameObject newCharacterPrefab = characterPrefabs[randomIndex];

        // 实例化新人物
        GameObject newCharacter = Instantiate(newCharacterPrefab, position, Quaternion.identity);

        // 尝试将新人物设置到 patient1 或 patient2 下
        bool assigned = false;

        if (patient1 != null && patient1.transform.childCount == 0)
        {
            newCharacter.transform.SetParent(patient1.transform);
            // 重置位置和旋转
            newCharacter.transform.localPosition = Vector3.zero;
            newCharacter.transform.localRotation = Quaternion.identity;
            assigned = true;

            // 传递当前积分给新人物
            newCharacter.GetComponent<CharacterSlot>().score = score;
        }
        else if (patient2 != null && patient2.transform.childCount == 0)
        {
            newCharacter.transform.SetParent(patient2.transform);
            // 重置位置和旋转
            newCharacter.transform.localPosition = Vector3.zero;
            newCharacter.transform.localRotation = Quaternion.identity;
            assigned = true;

            // 传递当前积分给新人物
            newCharacter.GetComponent<CharacterSlot>().score = score;
        }

        if (assigned)
        {
            characterCount++;
        }
        else
        {
            // 如果没有可用的 patient，则销毁新生成的人物
            Destroy(newCharacter);
            Debug.LogWarning("没有可用的 patient 来分配新人物");
        }
    }

    // 新增方法：修改积分
    public void ModifyScore(int amount)
    {
        score += amount;
        UpdateScoreUI();
        Debug.Log("积分修改: " + amount + ". 当前积分: " + score);
    }

    // 销毁多余的人物
    public void DestroyExcessCharacters()
    {
        // 检查 patient1 和 patient2 下的子物体数量
        if (patient1 != null && patient1.transform.childCount > 1)
        {
            // 销毁多余的人物
            foreach (Transform child in patient1.transform)
            {
                if (child != patient1.transform.GetChild(0))
                {
                    Destroy(child.gameObject);
                }
            }
        }

        if (patient2 != null && patient2.transform.childCount > 1)
        {
            // 销毁多余的人物
            foreach (Transform child in patient2.transform)
            {
                if (child != patient2.transform.GetChild(0))
                {
                    Destroy(child.gameObject);
                }
            }
        }
    }

    // 协程，定期检查并重新生成人物
    private IEnumerator CheckAndRespawnCharacters()
    {
        while (true)
        {
            // 检查 patient1 和 patient2 下的子物体数量
            if (patient1 != null && patient1.transform.childCount == 0)
            {
                SpawnNewCharacter();
            }

            if (patient2 != null && patient2.transform.childCount == 0)
            {
                SpawnNewCharacter();
            }

            // 每隔一段时间检查一次
            yield return new WaitForSeconds(1f);
        }
    }

    // 新增协程：倒计时
    private IEnumerator CountdownCoroutine()
    {
        if (currentGameMode == GameMode.TimedMode)
        {
            while (countdownTime > 0)
            {
                countdownTime -= Time.deltaTime;
                UpdateCountdownUI();
                yield return null;
            }

            // 倒计时结束，执行游戏结束逻辑
            if (gameOverPopup != null)
            {
                GameOver();
            }
            else
            {
                Debug.LogWarning("Game Over Popup 未设置，无法调用 GameOver()");
            }
        }
    }

    // 修改 GameOver 方法以添加按钮
    private void GameOver()
    {
        isGameOver = true;

        // 显示弹出窗口
        if (gameOverPopup != null)
        {
            gameOverPopup.SetActive(true);

            // 更新最终积分显示
            if (finalScoreText != null)
            {
                finalScoreText.text = "最终积分: " + score;
            }
            else
            {
                Debug.LogWarning("Final Score Text UI 未设置");
            }

            // 设置按钮的监听器
            if (restartButton != null)
            {
                restartButton.onClick.RemoveAllListeners();
                restartButton.onClick.AddListener(RestartGame);
                restartButton.gameObject.SetActive(true);
            }
            else
            {
                Debug.LogWarning("Restart Button 未设置");
            }

            if (mainMenuButton != null)
            {
                mainMenuButton.onClick.RemoveAllListeners();
                mainMenuButton.onClick.AddListener(LoadMainMenu);
                mainMenuButton.gameObject.SetActive(true);
            }
            else
            {
                Debug.LogWarning("Main Menu Button 未设置");
            }
        }
        else
        {
            Debug.LogWarning("Game Over Popup 未设置");
        }

        // 停止所有协程
        StopAllCoroutines();

        // 禁用所有交互
        craftButton.interactable = false;
        foreach (Slot slot in craftingSlots)
        {
            if (slot != null && slot.GetComponent<Button>() != null)
            {
                slot.GetComponent<Button>().interactable = false;
            }
            else
            {
                Debug.LogWarning("Slot 或其 Button 组件为空");
            }
        }

        // 显示游戏结束信息
        Debug.Log("游戏结束");
    }

    // 新增方法：重新开始当前场景
    public void RestartGame()
    {
        // 获取当前场景名称
        string currentSceneName = UnityEngine.SceneManagement.SceneManager.GetActiveScene().name;
        UnityEngine.SceneManagement.SceneManager.LoadScene(currentSceneName);
    }

    // 新增方法：加载主菜单场景
    public void LoadMainMenu()
    {
        // 替换 "MainMenuScene" 为你的主菜单场景名称
        UnityEngine.SceneManagement.SceneManager.LoadScene("MainMenuScene");
    }

    // 新增方法：处理错误的配方
    public void OnWrongRecipe()
    {
        if (currentGameMode == GameMode.InfiniteMode)
        {
            remainingWrongAttempts--;
            UpdateRemainingWrongAttemptsUI();
            if (remainingWrongAttempts <= 0)
            {
                GameOver();
            }
        }
        else
        {
            // 在限时模式下，不做任何处理
            Debug.Log("在限时模式下，错误的配方不会导致游戏结束。");
        }
    }
}