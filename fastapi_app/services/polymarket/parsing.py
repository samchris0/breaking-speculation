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
        market_id = market['id']
        
        # Check if market is active, open, and has volume
        market_closed = market["closed"]
        market_active = market["active"]
        volume = float(market.get('volume',0))

        # Check if the the market has a CLOB orderbook, otherwise price history not available
        if clobTokenIds and volume and market_active and not market_closed:
            tokenIds = json.loads(market['clobTokenIds'])


            if not volume:
                print(market)

            for i in range(len(outcomes)):
                next_market = {
                        'provider':'polymarket',
                        'event_id':event_id,
                        'event_title':event_title,
                        'event_image':event_image,
                        'market_id':market_id,
                        'market_question': market_question, 
                        'volume':volume,
                        'outcome':outcomes[i], 
                        'tokenId':tokenIds[i],
                        'volume':volume
                        }
                
                data.append(next_market)

    return data

def create_tree():

    tree = defaultdict(
        lambda: {
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

    return tree

def add_market_to_tree(tree: Dict, market: Dict) -> Dict:
    event_id = market['event_id']
    market_id = market['market_id']

    # Define event node
    event = tree[event_id]

    # Populate event node
    event["title"] = market["event_title"]
    event["image"] = market["event_image"]

    # Define market node
    market = event["markets"][market_id]  # type: ignore[index]

    #Populate market node
    market["question"] = market["market_question"]
    market["volume"] = market["volume"]
    market["outcomes"].append(  # type: ignore[index]
        {
            'provider':market['provider'],
            'tokenId':market['tokenId'],
            'outcome':market['outcome'],
            'history':market['history']
        }
    )

    return tree

def materialize_polymarket(flat_rows: List[Dict]) -> Dict: 
    
    # Create dict structure
    tree = defaultdict(
        lambda: {
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