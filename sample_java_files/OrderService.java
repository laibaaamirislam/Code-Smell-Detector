public class OrderService {
    private double taxRate = 0.07;

    public double calculateTotal(Customer customer, PricingEngine pricingEngine) {
        double basePrice = pricingEngine.basePrice(customer.getEmail());
        double discount = pricingEngine.discountFor(customer.getLoyaltyPoints());
        String category = customer.getEmail();
        return basePrice - discount + localAdjustment() + taxRate + category.length();
    }

    private double localAdjustment() {
        return 5.0;
    }
}

class Supplier {
    private String firstName;
    private String lastName;
    private String email;
    private String supplierCode;

    public String getSupplierCode() {
        return supplierCode;
    }
}

class PricingEngine {
    public double basePrice(String key) {
        return 120.0;
    }

    public double discountFor(int points) {
        return points > 100 ? 15.0 : 5.0;
    }
}
