using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using UnityEngine.UI;
using UnityEngine.TextCore.Text;
using System.Linq;

public class CraftingManager2 : MonoBehaviour
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

    // 新增错误计数变量
    private int errorCount = 0;
    public Text errorCountText; // 用于显示错误次数的 UI Text

    // 新增 UIManager 引用
    public UIManager uiManager;

    // 新增弹出窗口变量
    public GameObject gameOverPopup;
    public Text finalScoreText; // 用于显示最终积分的 Text
    public Text finalErrorCountText; // 用于显示最终错误次数的 Text

    // 新增按钮引用
    public Button restartButton;
    public Button mainMenuButton;

    private bool isGameOver = false;

    public int Score
    {
        get { return score; }
    }

    private void Start()
    {
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

        // 随机生成两个初始人物，并分别设置为 Patient1 和 Patient2 的子物体
        for (int i = 0; i < 2; i++)
        {
            SpawnNewCharacter();
        }

        // 启动一个协程，定期检查并重新生成人物
        StartCoroutine(CheckAndRespawnCharacters());

        // 初始化积分显示
        UpdateScoreUI();

        // 初始化错误计数显示
        UpdateErrorCountUI();

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

    // 新增方法：更新错误计数显示
    public void UpdateErrorCountUI()
    {
        if (errorCountText != null)
        {
            errorCountText.text = "错误次数: " + errorCount;
        }
        else
        {
            Debug.LogWarning("Error Count Text UI 未设置");
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

    private void Update()
    {
        // 这里可以处理拖拽相关逻辑
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
                recipeObject.GetComponent<DraggableItem2>().enabled = true;
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
        Debug.Log("OnClickSlot 被调用，槽位索引: " + slot.index);
        if (itemsList[slot.index] != null)
        {
            itemsList[slot.index] = null;
            Destroy(slot.transform.GetChild(0).gameObject); // 销毁卡牌物体
            slot.item = null; // 移除卡牌
            CheckForCreatedRecipesAlternative(); // 调用重命名后的方法
            Debug.Log("从槽位移除物品: " + slot.index);
        }
        else
        {
            Debug.Log("槽位中没有物品，槽位索引: " + slot.index);
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
        bool isMatch = false;
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

            bool localMatch = true;
            // 检查当前配方是否包含所有药材，并且数量匹配
            foreach (var kvp in recipeDict)
            {
                if (!currentRecipeDict.ContainsKey(kvp.Key) || currentRecipeDict[kvp.Key] < kvp.Value)
                {
                    localMatch = false;
                    break;
                }
            }

            if (localMatch)
            {
                isMatch = true;
                // 实例化药方卡牌作为resultSlot的子对象
                string recipeName = recipeResult[System.Array.IndexOf(recipes, recipe)].recipeName;
                GameObject recipeObject = Instantiate(recipeResult[System.Array.IndexOf(recipes, recipe)].gameObject, resultSlot.transform);
                recipeObject.transform.localPosition = Vector3.zero;
                recipeObject.GetComponent<Image>().sprite = recipeResult[System.Array.IndexOf(recipes, recipe)].GetComponent<Image>().sprite;
                recipeObject.GetComponent<Item>().isRecipe = true;
                recipeObject.GetComponent<Item>().recipeName = recipeName;
                // 设置药方卡牌的可拖拽属性
                recipeObject.GetComponent<DraggableItem2>().enabled = true;
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

                // 增加积分
                ModifyScore(10); // 假设每合成一个配方增加10积分

                break;
            }
        }

        if (!isMatch)
        {
            // 如果配方不匹配，增加错误计数
            errorCount++;
            UpdateErrorCountUI();
            Debug.Log("配方不匹配，增加错误计数: " + errorCount);

            // 检查是否达到最大错误次数
            if (errorCount >= 3)
            {
                GameOver();
            }
        }
    }

    public void OnDropIncorrectRecipe()
    {
        errorCount++;
        UpdateErrorCountUI();
        Debug.Log("将错误药方拖给客人，增加错误计数: " + errorCount);

        // 检查是否达到最大错误次数
        if (errorCount >= 3)
        {
            GameOver();
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

            // 更新最终错误次数显示
            if (finalErrorCountText != null)
            {
                finalErrorCountText.text = "错误次数: " + errorCount;
            }
            else
            {
                Debug.LogWarning("Final Error Count Text UI 未设置");
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

    // 修改 CheckForCreatedRecipes 方法以处理配方生成失败的情况
    void CheckForCreatedRecipesAlternative()
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
                recipeObject.GetComponent<DraggableItem2>().enabled = true;
                Debug.Log("生成配方卡牌: " + recipeName);
                break;
            }
        }
    }
}