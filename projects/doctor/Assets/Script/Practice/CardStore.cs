using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class CardStore : MonoBehaviour
{
    public TextAsset cardData;
    public List<Card> cardList = new List<Card>();

    // Start is called before the first frame update
    void Start()
    {
        LoadCardData();
        TextLoad();
    }

    // Update is called once per frame
    void Update()
    {
        
    }
    public void LoadCardData()
    {
        string[] dataRow = cardData.text.Split('\n');
        foreach (var row in dataRow)
        {
            string[] rowArray = row.Split(',');
            if (rowArray[0] == "#")
            {
                continue;
            }
            else if (rowArray[0] == "monster")
            {
                //create a new monster card
                int id = int.Parse(rowArray[1]);
                string name = rowArray[2];
                int atk = int.Parse(rowArray[3]);
                int health = int.Parse(rowArray[4]);
                MonsterCard monsterCard = new MonsterCard(id, name, atk, health);
                cardList.Add(monsterCard);

                Debug.Log("读取到怪兽卡" + monsterCard.cardName);
            }
            else if (rowArray[0] == "spell")
            {
                //create a new spell card
                int id = int.Parse(rowArray[1]);
                string name = rowArray[2];
                string effect = rowArray[3];
                SpellCard spellCard = new SpellCard(id, name, effect);
                cardList.Add(spellCard);
            }
        }
    }
    public void TextLoad()
{
    foreach (var card in cardList)
    {
        Debug.Log("卡牌名称：" + card.id.ToString() + card.cardName);
    }
}
    public Card RandomCard()
    {
        Card card = cardList[Random.Range(0, cardList.Count)];
        return card;
    }
}
