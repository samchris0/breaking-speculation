import json
from collections import defaultdict
from typing import Any, Dict, List

def polymarket_get_market_ids(event: Dict[str, Any]) -> List[Dict]:
    """
    Takes events slug query response and extracts relevant data to query price history
    """

    data = []
    event_title = event['title']
    event_id = event['id']
    markets = event['markets']
    event_image = event['image']
    for market in markets:
        
        market_question = market['question']
        
        # Polymarket API wraps these lists with a string "["...", "..."]"
        outcomes = json.loads(market['outcomes'])
        clobTokenIds = market.get('clobTokenIds',[])
        volume = market['volumeNum']
        market_id = market['id']
        
        # Check if the the market has a CLOB orderbook, otherwise price history not available
        if clobTokenIds:
            tokenIds = json.loads(market['clobTokenIds'])

            for i in range(len(outcomes)):
                next_market = {
                        'provider':'polymarket',
                        'event_id':event_id,
                        'event_title':event_title,
                        'event_image':event_image,
                        'market_id':market_id,
                        'market_question': market_question, 
                        'outcome':outcomes[i], 
                        'tokenId':tokenIds[i],
                        'volume':volume
                        }
                
                data.append(next_market)

    return data


def materialize_polymarket(flat_rows: List[Dict]) -> Dict: 
    
    # Create 
    tree = defaultdict(
        lambda: {
            #might not be necessary
            "title": None,
            "image":None,
            "markets": defaultdict(
                lambda: {
                    "question": None,
                    "volume":None,
                    "outcomes": []
                }
            )
        }
    )

    for row in flat_rows:
        event_id = row['event_id']
        market_id = row['market_id']

        # Define event node
        event = tree[event_id]

        # Populate event node
        event["title"] = row["event_title"]
        event["image"] = row["event_image"]

        # Define market node
        market = event["markets"][market_id]  # type: ignore[index]

        #Populate market node
        market["question"] = row["market_question"]
        market["volume"] = row["volume"]
        market["outcomes"].append(  # type: ignore[index]
            {
                'provider':row['provider'],
                'tokenId':row['tokenId'],
                'outcome':row['outcome'],
                'history':row['history']
            }
        )
    
    return tree
