def make_records_collection(mongo_url: str, db_name: str):
    import pymongo

    client = pymongo.MongoClient(mongo_url)
    return client[db_name]["records"]
