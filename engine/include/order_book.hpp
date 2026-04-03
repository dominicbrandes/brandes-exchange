#pragma once
#include <cstdint>
#include <string>
#include <map>
#include <unordered_map>
#include <vector>
#include <optional>

namespace brandes {

using Price = int64_t;
using Quantity = int64_t;
using OrderId = uint64_t;
using Timestamp = uint64_t;

constexpr int64_t SCALE = 100000000;

enum class Side { BUY, SELL };
enum class OrderStatus { NEW, PARTIAL, FILLED, CANCELLED, REJECTED };

struct Order {
    OrderId id;
    std::string account_id;
    std::string symbol;
    Side side;
    Price price;
    Quantity quantity;
    Quantity remaining_qty;
    OrderStatus status;
    Timestamp timestamp_ns;
    std::string reject_reason;
};

struct Trade {
    uint64_t id;
    std::string symbol;
    Price price;
    Quantity quantity;
    Timestamp timestamp_ns;
    std::string buyer_account_id;
    std::string seller_account_id;
    OrderId buy_order_id;
    OrderId sell_order_id;
};

struct Level {
    Price price;
    Quantity quantity;
};

class OrderBook {
public:
    explicit OrderBook(const std::string& symbol);
    std::pair<Order, std::vector<Trade>> place_order(
        const std::string& account_id, Side side, Price price, Quantity quantity);
    std::optional<Order> cancel_order(OrderId order_id);
    std::vector<Level> get_bids(size_t depth = 50) const;
    std::vector<Level> get_asks(size_t depth = 50) const;
    std::optional<Order> get_order(OrderId order_id) const;
    uint64_t get_sequence() const { return sequence_; }
    void clear();

private:
    std::string symbol_;
    uint64_t sequence_ = 0;
    OrderId next_order_id_ = 1;
    uint64_t next_trade_id_ = 1;
    std::map<Price, std::vector<Order*>, std::greater<Price>> bids_;
    std::map<Price, std::vector<Order*>, std::less<Price>> asks_;
    std::unordered_map<OrderId, Order> orders_;
    std::vector<Trade> match_order(Order& order);
    void add_to_book(Order& order);
    void remove_from_book(Order& order);
    Timestamp now_ns() const;
};

}
