using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class CardDisplay : MonoBehaviour
{
    public Text nameText;
    public Text attackText;
    public Text healthText;
    public Text effectText;

    public Card card;

    public Image backgroundImage;
    // Start is called before the first frame update
    void Start()
    {
       showCard(); 
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    public void showCard()
    {
        nameText.text = card.cardName;
        if(card is MonsterCard)
        {
            var monsterCard = card as MonsterCard;
            attackText.text = monsterCard.attack.ToString();
            healthText.text = monsterCard.healthPoint.ToString();
            
            effectText.gameObject.SetActive(false);
        }
        else if(card is SpellCard)
        {
            var spellCard = card as SpellCard;
            effectText.text = spellCard.effect;
        }
        
        attackText.gameObject.SetActive(false);
        healthText.gameObject.SetActive(false);
    }
}
