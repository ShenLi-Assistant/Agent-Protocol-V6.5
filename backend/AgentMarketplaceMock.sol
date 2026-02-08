// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title AgentMarketplaceMock
 * @notice Mock contract that demonstrates core Agent Protocol bounty mechanics:
 *         - USDC balance tracking (mocked internal ledger)
 *         - 10% stake requirement when claiming a bounty
 *         - On-chain work hash verification
 */
contract AgentMarketplaceMock {
    uint256 public constant STAKE_BPS = 1000; // 10.00%
    uint256 public constant BPS_DENOMINATOR = 10_000;

    error Unauthorized();
    error ZeroAddress();
    error InvalidAmount();
    error BountyAlreadyClaimed(uint256 bountyId);
    error BountyNotClaimed(uint256 bountyId);
    error AlreadyVerified(uint256 bountyId);
    error InsufficientBalance(address agent, uint256 required, uint256 available);

    struct Bounty {
        address agent;
        uint256 stakeAmount;
        bytes32 expectedWorkHash;
        bool claimed;
        bool verified;
    }

    address public immutable owner;
    mapping(address => uint256) private usdcBalances;
    mapping(uint256 => Bounty) private bounties;

    event USDCSeeded(address indexed wallet, uint256 amount, uint256 newBalance);
    event BountyClaimed(uint256 indexed bountyId, address indexed agent, uint256 stakeAmount, bytes32 expectedWorkHash);
    event WorkVerified(uint256 indexed bountyId, address indexed agent, bytes32 deliveredWorkHash, uint256 rewardAmount);
    event WorkVerificationFailed(uint256 indexed bountyId, bytes32 expectedWorkHash, bytes32 deliveredWorkHash);

    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Seed mock USDC to a wallet for local/demo environments.
     */
    function seedUSDC(address wallet, uint256 amount) external onlyOwner {
        if (wallet == address(0)) revert ZeroAddress();
        if (amount == 0) revert InvalidAmount();

        usdcBalances[wallet] += amount;
        emit USDCSeeded(wallet, amount, usdcBalances[wallet]);
    }

    function usdcBalanceOf(address wallet) external view returns (uint256) {
        return usdcBalances[wallet];
    }

    function getBounty(uint256 bountyId) external view returns (Bounty memory) {
        return bounties[bountyId];
    }

    function requiredStake(address wallet) public view returns (uint256) {
        return (usdcBalances[wallet] * STAKE_BPS) / BPS_DENOMINATOR;
    }

    /**
     * @notice Agent claims bounty and stakes exactly 10% of current USDC balance.
     */
    function claimBounty(uint256 bountyId, bytes32 expectedWorkHash) external returns (uint256 stakeAmount) {
        Bounty storage bounty = bounties[bountyId];
        if (bounty.claimed) revert BountyAlreadyClaimed(bountyId);

        uint256 balance = usdcBalances[msg.sender];
        stakeAmount = (balance * STAKE_BPS) / BPS_DENOMINATOR;
        if (stakeAmount == 0) revert InsufficientBalance(msg.sender, 1, balance);

        usdcBalances[msg.sender] = balance - stakeAmount;

        bounty.agent = msg.sender;
        bounty.stakeAmount = stakeAmount;
        bounty.expectedWorkHash = expectedWorkHash;
        bounty.claimed = true;

        emit BountyClaimed(bountyId, msg.sender, stakeAmount, expectedWorkHash);
    }

    /**
     * @notice Owner/orchestrator verifies that delivered hash matches expected hash.
     *         Successful verification credits mock payout to the agent.
     */
    function verifyWorkDelivery(uint256 bountyId, bytes32 deliveredWorkHash) external onlyOwner returns (bool) {
        Bounty storage bounty = bounties[bountyId];
        if (!bounty.claimed) revert BountyNotClaimed(bountyId);
        if (bounty.verified) revert AlreadyVerified(bountyId);

        if (bounty.expectedWorkHash != deliveredWorkHash) {
            emit WorkVerificationFailed(bountyId, bounty.expectedWorkHash, deliveredWorkHash);
            return false;
        }

        bounty.verified = true;

        uint256 rewardAmount = bounty.stakeAmount * 2;
        usdcBalances[bounty.agent] += rewardAmount;

        emit WorkVerified(bountyId, bounty.agent, deliveredWorkHash, rewardAmount);
        return true;
    }
}
