# formatter.py
from datetime import datetime

def format_scraped_data(raw_dict):
    metal_map = {
        "18KT WG": "18K White Gold",
        "18KT YG": "18K Yellow Gold",
        "18KT RG": "18K Rose Gold",
        "Platinum": "Platinum"
    }

    return {
        "website": "77Diamonds",
        "product_url": raw_dict.get("product_url", ""),
        "category": raw_dict.get("category", ""),
        "sub_category": raw_dict.get("sub_category", ""),
        "collection_no": raw_dict.get("collection_no", ""),
        "variant_no": "",
        "metal": metal_map.get(raw_dict.get("metal", "").strip(), raw_dict.get("metal", "")),
        "stone_type": raw_dict.get("stone_type", ""),
        "stone_shape": raw_dict.get("stone_shape", ""),
        "stone_carat": raw_dict.get("stone_carat", ""),
        "color": raw_dict.get("color", ""),
        "clarity": raw_dict.get("clarity", ""),
        "cut": raw_dict.get("cut", ""),
        "product_title": raw_dict.get("product_title", ""),
        "metal_price": raw_dict.get("metal_price", ""),
        "stone_price": raw_dict.get("stone_price", ""),
        "final_price": raw_dict.get("final_price", ""),
        "updated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "setting_title": raw_dict.get("setting_title", ""),
        "setting_price": raw_dict.get("setting_price", ""),
        "diamond_title": raw_dict.get("diamond_title", ""),
        "product_description": raw_dict.get("product_description", ""),
        "additional_attributes": raw_dict.get("additional_attributes", ""),
        "metal_t": "", "stone_type_t": "", "stone_shape_t": "",
        "clarity_t": "", "cut_t": "", "metal_price_e": "",
        "stone_price_e": "", "final_price_e": "", "updated_date_t": "",
        "additional_title": "", "final_title": ""
    }
