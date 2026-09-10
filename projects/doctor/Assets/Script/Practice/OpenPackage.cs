using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class OpenPackage : MonoBehaviour
{
    public GameObject cardPrefab;
    public GameObject CardPool;
    CardStore CardStore;
    List<GameObject> cards = new List<GameObject>();
    // Start is called before the first frame update
    void Start()
    {
        CardStore = GetComponent<CardStore>();
    }

    // Update is called once per frame
    void Update()
    {
        
    }
    public void OnClickOpen()
    {
        ClearPool();
       for(int i = 0; i < 5; i++)
       {
        GameObject newCard = GameObject.Instantiate(cardPrefab, CardPool.transform);
        newCard.GetComponent<CardDisplay>().card = CardStore.RandomCard();

        cards.Add(newCard);
       }
    }
    public void ClearPool()
    {
        foreach(var card in cards)
        {
            GameObject.Destroy(card);
        }
        cards.Clear();
    }
}
