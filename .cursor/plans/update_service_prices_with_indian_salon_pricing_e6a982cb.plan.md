---
name: Update Service Prices with Indian Salon Pricing
overview: Update all 48 services with realistic Indian salon pricing based on service type, complexity, and typical market rates in India.
todos:
  - id: prepare_pricing_data
    content: Prepare pricing data for all 48 services organized by category
    status: pending
  - id: update_body_spa_prices
    content: Update prices for Body Spa & Massage services (3 services)
    status: pending
    dependencies:
      - prepare_pricing_data
  - id: update_hair_care_prices
    content: Update prices for Hair Care & Treatments services (14 services)
    status: pending
    dependencies:
      - prepare_pricing_data
  - id: update_facial_prices
    content: Update prices for Facial Services (18 services)
    status: pending
    dependencies:
      - prepare_pricing_data
  - id: update_pedicure_prices
    content: Update prices for Manicure & Pedicure services (3 services)
    status: pending
    dependencies:
      - prepare_pricing_data
  - id: update_threading_prices
    content: Update prices for Threading & Face Care services (3 services)
    status: pending
    dependencies:
      - prepare_pricing_data
  - id: update_waxing_prices
    content: Update prices for Waxing Services (2 services)
    status: pending
    dependencies:
      - prepare_pricing_data
  - id: update_bleach_prices
    content: Update prices for Bleach Services (5 services)
    status: pending
    dependencies:
      - prepare_pricing_data
  - id: verify_all_prices
    content: Verify all 48 services have been updated with correct pricing
    status: pending
    dependencies:
      - update_body_spa_prices
      - update_hair_care_prices
      - update_facial_prices
      - update_pedicure_prices
      - update_threading_prices
      - update_waxing_prices
      - update_bleach_prices
---

# Update Service Prices with Indian Salon Pricing

## Overview

Update all 48 services in MongoDB with realistic pricing based on Indian salon standards. Prices will reflect the service type, complexity, and typical market rates in India.

## Pricing Strategy

### Price Ranges by Category:

1. **Basic Services (Threading, Cleanup)**: ₹50 - ₹500
2. **Hair Care Basic (Wash, Conditioning)**: ₹200 - ₹800
3. **Hair Treatments (Straightening, Rebonding)**: ₹2000 - ₹8000
4. **Facial Services Basic**: ₹500 - ₹2000
5. **Facial Services Premium**: ₹1500 - ₹5000
6. **Massage Services**: ₹800 - ₹2500
7. **Pedicure Services**: ₹500 - ₹1500
8. **Waxing Services**: ₹300 - ₹1500
9. **Bleach Services**: ₹400 - ₹2000

## Service Pricing Details

### Body Spa & Massage (3 services)

- **Olive Oil Massage**: ₹800 (60 min, basic massage)
- **Almond Massage**: ₹1200 (60 min, premium oil)
- **Aroma Massage**: ₹1500 (60 min, aromatherapy)

### Hair Care & Treatments (14 services)

- **Shampoo Wash**: ₹200 (basic wash)
- **Conditioning**: ₹300 (standard conditioning)
- **Deep Conditioning**: ₹500 (deep treatment)
- **Dandruff Treatment**: ₹600 (therapeutic)
- **Hair Fall Treatment**: ₹800 (premium treatment)
- **Hair Spa Care**: ₹1500 (full spa experience)
- **Straightening**: ₹3500 (chemical treatment)
- **Rebonding**: ₹4500 (premium straightening)
- **Hair Coloring**: ₹2500 (standard coloring)
- **Henna Coloring**: ₹800 (natural henna)
- **Henna Conditioning**: ₹600 (henna treatment)
- **Black Henna**: ₹1000 (premium henna)
- **Nano Plex Protein Treatment**: ₹2000 (advanced treatment)
- **Botox Treatment**: ₹3500 (premium hair botox)

### Facial Services (18 services)

- **Glow Derma Facial**: ₹2500 (derma facial)
- **Depigmentation**: ₹2000 (specialized treatment)
- **Derma Peel**: ₹1800 (peel treatment)
- **Insta Face Lift**: ₹3000 (premium facial)
- **Skin Polishing**: ₹1500 (basic polishing)
- **White Miracle Facial**: ₹2000 (whitening facial)
- **Choco Wine Facial**: ₹2200 (premium facial)
- **4 Layers Radiance**: ₹2800 (4-step treatment)
- **4 Layers Whitening**: ₹2800 (4-step whitening)
- **4 Layers Anti Ageing**: ₹3200 (4-step anti-ageing)
- **Vino Grapes Facial**: ₹2000 (grape facial)
- **Pineapple Facial**: ₹1200 (fruit facial)
- **Papaya Facial**: ₹1200 (fruit facial)
- **Kiwi Facial**: ₹1200 (fruit facial)
- **Beaberry Facial**: ₹1300 (premium fruit facial)
- **Herbal Facial**: ₹1500 (herbal treatment)
- **Fruit Facial**: ₹1000 (basic fruit facial)
- **Under Eye Treatment**: ₹800 (targeted treatment)

### Manicure & Pedicure (3 services)

- **Spa Pedicure with Essential Oils**: ₹1200 (premium pedicure)
- **Blue Berry Pedicure**: ₹1000 (specialized pedicure)
- **Crystal Spa Pedicure**: ₹1500 (luxury pedicure)

### Threading & Face Care (3 services)

- **Thread**: ₹50 (basic threading)
- **Cleanup**: ₹500 (face cleanup)
- **Shahnaz Veg Peel**: ₹800 (premium peel)

### Waxing Services (2 services)

- **Honey Wax**: ₹600 (premium waxing)
- **Rica Wax**: ₹700 (specialized wax)

### Bleach Services (5 services)

- **Oxy Bleach**: ₹500 (standard bleach)
- **Aroma Bleach**: ₹600 (premium bleach)
- **Lacto Bleach**: ₹550 (gentle bleach)
- **Gold Bleach**: ₹800 (premium gold bleach)
- **Tan Bleach**: ₹700 (tan removal bleach)

## Implementation Steps

1. **Prepare Pricing Updates**: Create update operations for each service with new pricing
2. **Update Services**: Use MCP MongoDB update operations to set prices for all 48 services
3. **Verify Pricing**: Confirm all services have been updated with correct prices

## Technical Details

- **Database**: Saloon_prod
- **Collection**: `services`
- **Tool**: MCP MongoDB update-many operations
- **Currency**: Indian Rupees (₹)

## Notes

- Prices reflect mid-range to premium salon standards in India
- Premium treatments (Rebonding, Botox, Anti-Ageing) have higher pricing
- Basic services (Thread, Cleanup) have lower pricing
- All prices are in Indian Rupees (₹)