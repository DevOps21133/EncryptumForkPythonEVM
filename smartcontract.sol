//
// *Submitted for verification at Etherscan.io on 2025-05-31
//

// File: @openzeppelin/contracts/utils/Context.sol
/**
$$$$$$$\                             $$$$$$\                                       
$$  __$$\                           $$$ __$$\            $$\$$\   $$\$$\   $$\$$\  
$$ |  $$ | $$$$$$\ $$\    $$\       $$$$\ $$ |$$\   $$\  \$$$  |  \$$$  |  \$$$  | 
$$ |  $$ |$$  __$$\\$$\  $$  |      $$\$$\$$ |\$$\ $$  |$$$$$$$\ $$$$$$$\ $$$$$$$\ 
$$ |  $$ |$$$$$$$$ |\$$\$$  /       $$ \$$$$ | \$$$$  / \_$$$ __|\_$$$ __|\_$$$ __|
$$ |  $$ |$$   ____| \$$$  /        $$ |\$$$ | $$  $$<   $$ $$\   $$ $$\   $$ $$\  
$$$$$$$  |\$$$$$$$\   \$  /         \$$$$$$  /$$  /\$$\  \__\__|  \__\__|  \__\__| 
\_______/  \_______|   \_/           \______/ \__/  \__|                           
*/
// OpenZeppelin Contracts (last updated v5.0.1) (utils/Context.sol)

pragma solidity ^0.8.20;

/**
 * @dev Provides information about the current execution context, including the
 * sender of the transaction and its data. While these are generally available
 * via msg.sender and msg.data, they should not be accessed in such a direct
 * manner, since when dealing with meta-transactions the account sending and
 * paying for execution may not be the actual sender (as far as an application
 * is concerned).
 *
 * This contract is only required for intermediate, library-like contracts.
 */
abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes calldata) {
        return msg.data;
    }

    function _contextSuffixLength() internal view virtual returns (uint256) {
        return 0;
    }
}

// File: @openzeppelin/contracts/access/Ownable.sol


// OpenZeppelin Contracts (last updated v5.0.0) (access/Ownable.sol)

pragma solidity ^0.8.20;


/**
 * @dev Contract module which provides a basic access control mechanism, where
 * there is an account (an owner) that can be granted exclusive access to
 * specific functions.
 *
 * The initial owner is set to the address provided by the deployer. This can
 * later be changed with {transferOwnership}.
 *
 * This module is used through inheritance. It will make available the modifier
 * `onlyOwner`, which can be applied to your functions to restrict their use to
 * the owner.
 */
abstract contract Ownable is Context {
    address private _owner;

    /**
     * @dev The caller account is not authorized to perform an operation.
     */
    error OwnableUnauthorizedAccount(address account);

    /**
     * @dev The owner is not a valid owner account. (eg. `address(0)`)
     */
    error OwnableInvalidOwner(address owner);

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    /**
     * @dev Initializes the contract setting the address provided by the deployer as the initial owner.
     */
    constructor(address initialOwner) {
        if (initialOwner == address(0)) {
            revert OwnableInvalidOwner(address(0));
        }
        _transferOwnership(initialOwner);
    }

    /**
     * @dev Throws if called by any account other than the owner.
     */
    modifier onlyOwner() {
        _checkOwner();
        _;
    }

    /**
     * @dev Returns the address of the current owner.
     */
    function owner() public view virtual returns (address) {
        return _owner;
    }

    /**
     * @dev Throws if the sender is not the owner.
     */
    function _checkOwner() internal view virtual {
        if (owner() != _msgSender()) {
            revert OwnableUnauthorizedAccount(_msgSender());
        }
    }

    /**
     * @dev Leaves the contract without owner. It will not be possible to call
     * `onlyOwner` functions. Can only be called by the current owner.
     *
     * NOTE: Renouncing ownership will leave the contract without an owner,
     * thereby disabling any functionality that is only available to the owner.
     */
    function renounceOwnership() public virtual onlyOwner {
        _transferOwnership(address(0));
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Can only be called by the current owner.
     */
    function transferOwnership(address newOwner) public virtual onlyOwner {
        if (newOwner == address(0)) {
            revert OwnableInvalidOwner(address(0));
        }
        _transferOwnership(newOwner);
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Internal function without access restriction.
     */
    function _transferOwnership(address newOwner) internal virtual {
        address oldOwner = _owner;
        _owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}

// File: @openzeppelin/contracts/security/ReentrancyGuard.sol


// OpenZeppelin Contracts (last updated v4.9.0) (security/ReentrancyGuard.sol)

pragma solidity ^0.8.0;

/**
 * @dev Contract module that helps prevent reentrant calls to a function.
 *
 * Inheriting from `ReentrancyGuard` will make the {nonReentrant} modifier
 * available, which can be applied to functions to make sure there are no nested
 * (reentrant) calls to them.
 *
 * Note that because there is a single `nonReentrant` guard, functions marked as
 * `nonReentrant` may not call one another. This can be worked around by making
 * those functions `private`, and then adding `external` `nonReentrant` entry
 * points to them.
 *
 * TIP: If you would like to learn more about reentrancy and alternative ways
 * to protect against it, check out our blog post
 * https://blog.openzeppelin.com/reentrancy-after-istanbul/[Reentrancy After Istanbul].
 */
abstract contract ReentrancyGuard {
    // Booleans are more expensive than uint256 or any type that takes up a full
    // word because each write operation emits an extra SLOAD to first read the
    // slot's contents, replace the bits taken up by the boolean, and then write
    // back. This is the compiler's defense against contract upgrades and
    // pointer aliasing, and it cannot be disabled.

    // The values being non-zero value makes deployment a bit more expensive,
    // but in exchange the refund on every call to nonReentrant will be lower in
    // amount. Since refunds are capped to a percentage of the total
    // transaction's gas, it is best to keep them low in cases like this one, to
    // increase the likelihood of the full refund coming into effect.
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;

    uint256 private _status;

    constructor() {
        _status = _NOT_ENTERED;
    }

    /**
     * @dev Prevents a contract from calling itself, directly or indirectly.
     * Calling a `nonReentrant` function from another `nonReentrant`
     * function is not supported. It is possible to prevent this from happening
     * by making the `nonReentrant` function external, and making it call a
     * `private` function that does the actual work.
     */
    modifier nonReentrant() {
        _nonReentrantBefore();
        _;
        _nonReentrantAfter();
    }

    function _nonReentrantBefore() private {
        // On the first call to nonReentrant, _status will be _NOT_ENTERED
        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");

        // Any calls to nonReentrant after this point will fail
        _status = _ENTERED;
    }

    function _nonReentrantAfter() private {
        // By storing the original value once again, a refund is triggered (see
        // https://eips.ethereum.org/EIPS/eip-2200)
        _status = _NOT_ENTERED;
    }

    /**
     * @dev Returns true if the reentrancy guard is currently set to "entered", which indicates there is a
     * `nonReentrant` function in the call stack.
     */
    function _reentrancyGuardEntered() internal view returns (bool) {
        return _status == _ENTERED;
    }
}

// File: @openzeppelin/contracts/security/Pausable.sol


// OpenZeppelin Contracts (last updated v4.7.0) (security/Pausable.sol)

pragma solidity ^0.8.0;


/**
 * @dev Contract module which allows children to implement an emergency stop
 * mechanism that can be triggered by an authorized account.
 *
 * This module is used through inheritance. It will make available the
 * modifiers `whenNotPaused` and `whenPaused`, which can be applied to
 * the functions of your contract. Note that they will not be pausable by
 * simply including this module, only once the modifiers are put in place.
 */
abstract contract Pausable is Context {
    /**
     * @dev Emitted when the pause is triggered by `account`.
     */
    event Paused(address account);

    /**
     * @dev Emitted when the pause is lifted by `account`.
     */
    event Unpaused(address account);

    bool private _paused;

    /**
     * @dev Initializes the contract in unpaused state.
     */
    constructor() {
        _paused = false;
    }

    /**
     * @dev Modifier to make a function callable only when the contract is not paused.
     *
     * Requirements:
     *
     * - The contract must not be paused.
     */
    modifier whenNotPaused() {
        _requireNotPaused();
        _;
    }

    /**
     * @dev Modifier to make a function callable only when the contract is paused.
     *
     * Requirements:
     *
     * - The contract must be paused.
     */
    modifier whenPaused() {
        _requirePaused();
        _;
    }

    /**
     * @dev Returns true if the contract is paused, and false otherwise.
     */
    function paused() public view virtual returns (bool) {
        return _paused;
    }

    /**
     * @dev Throws if the contract is paused.
     */
    function _requireNotPaused() internal view virtual {
        require(!paused(), "Pausable: paused");
    }

    /**
     * @dev Throws if the contract is not paused.
     */
    function _requirePaused() internal view virtual {
        require(paused(), "Pausable: not paused");
    }

    /**
     * @dev Triggers stopped state.
     *
     * Requirements:
     *
     * - The contract must not be paused.
     */
    function _pause() internal virtual whenNotPaused {
        _paused = true;
        emit Paused(_msgSender());
    }

    /**
     * @dev Returns to normal state.
     *
     * Requirements:
     *
     * - The contract must be paused.
     */
    function _unpause() internal virtual whenPaused {
        _paused = false;
        emit Unpaused(_msgSender());
    }
}

// File: encryptum.sol


pragma solidity ^0.8.19;




/**
 * @title EncryptumPinning
 * @notice Smart contract for decentralized IPFS pinning with payment
 * @dev Manages IPFS CID pinning with ETH payments and duration tracking
 */
contract EncryptumPinning is Ownable, ReentrancyGuard, Pausable {
    
    // Structs
    struct PinInfo {
        string fileCID;          // IPFS content identifier for file
        string metadataCID;      // IPFS content identifier for metadata
        address pinner;          // Address that paid for pinning
        uint256 pinStartTime;    // Timestamp when pinning started
        uint256 pinDuration;     // Duration in seconds
        uint256 fileSize;        // File size in bytes
        uint256 amountPaid;      // Amount paid in wei
        bool isActive;           // Whether pin is active
        string encryptedName;    // Encrypted file name for reference
    }
    
    struct PinnerStats {
        uint256 totalPins;       // Total number of pins by user
        uint256 totalSpent;      // Total amount spent on pinning
        uint256 totalSize;       // Total size of pinned files
    }
    
    // State variables
    mapping(bytes32 => PinInfo) public pins;              // pinId => PinInfo
    mapping(address => bytes32[]) public userPins;        // user => array of pinIds
    mapping(address => PinnerStats) public pinnerStats;   // user => stats
    mapping(string => bytes32) public cidToPinId;         // CID => pinId
    
    uint256 public pricePerGBPerDay = 0.0001 ether;       // Price in ETH per GB per day
    uint256 public minimumPinDuration = 30 days;          // Minimum pin duration
    uint256 public maximumPinDuration = 365 days;         // Maximum pin duration
    uint256 public totalPinsCount;                        // Total number of pins
    uint256 public totalActiveSize;                       // Total size of active pins
    
    address public treasury;                              // Treasury address for fees
    uint256 public treasuryFeePercent = 5;               // 5% fee to treasury
    
    // Events
    event FilePinned(
        bytes32 indexed pinId,
        address indexed pinner,
        string fileCID,
        string metadataCID,
        uint256 duration,
        uint256 amountPaid
    );
    
    event PinExtended(
        bytes32 indexed pinId,
        address indexed extender,
        uint256 additionalDuration,
        uint256 additionalPayment
    );
    
    event PinRemoved(
        bytes32 indexed pinId,
        address indexed remover
    );
    
    event PriceUpdated(uint256 newPricePerGBPerDay);
    event TreasuryUpdated(address newTreasury);
    
    // Modifiers
    modifier validDuration(uint256 duration) {
        require(
            duration >= minimumPinDuration && duration <= maximumPinDuration,
            "Invalid pin duration"
        );
        _;
    }
    
    modifier pinExists(bytes32 pinId) {
        require(pins[pinId].isActive, "Pin does not exist or is inactive");
        _;
    }
    
    constructor(address _treasury) Ownable(msg.sender) {
        treasury = _treasury;
    }
    
    /**
     * @notice Calculate pinning cost based on file size and duration
     * @param fileSize Size of file in bytes
     * @param duration Duration in seconds
     * @return cost Cost in wei
     */
    function calculatePinCost(uint256 fileSize, uint256 duration) 
        public 
        view 
        returns (uint256) 
    {
        // Convert file size to GB (with precision)
        uint256 sizeInGB = (fileSize * 1e18) / (1024 ** 3);
        
        // Convert duration to days
        uint256 durationInDays = duration / 1 days;
        
        // Calculate base cost
        uint256 baseCost = (sizeInGB * pricePerGBPerDay * durationInDays) / 1e18;
        
        // Add treasury fee
        uint256 treasuryFee = (baseCost * treasuryFeePercent) / 100;
        
        return baseCost + treasuryFee;
    }
    
    /**
     * @notice Pin a file on IPFS by paying ETH
     * @param fileCID IPFS CID of the encrypted file
     * @param metadataCID IPFS CID of the metadata
     * @param fileSize Size of file in bytes
     * @param duration Pin duration in seconds
     * @param encryptedName Encrypted file name for reference
     */
    function pinFile(
        string memory fileCID,
        string memory metadataCID,
        uint256 fileSize,
        uint256 duration,
        string memory encryptedName
    ) 
        external 
        payable 
        nonReentrant 
        whenNotPaused
        validDuration(duration)
    {
        require(bytes(fileCID).length > 0, "Invalid file CID");
        require(bytes(metadataCID).length > 0, "Invalid metadata CID");
        require(fileSize > 0, "Invalid file size");
        
        // Check if CID is already pinned
        require(cidToPinId[fileCID] == bytes32(0), "File already pinned");
        
        // Calculate required payment
        uint256 requiredPayment = calculatePinCost(fileSize, duration);
        require(msg.value >= requiredPayment, "Insufficient payment");
        
        // Generate unique pin ID
        bytes32 pinId = keccak256(
            abi.encodePacked(fileCID, msg.sender, block.timestamp)
        );
        
        // Create pin record
        pins[pinId] = PinInfo({
            fileCID: fileCID,
            metadataCID: metadataCID,
            pinner: msg.sender,
            pinStartTime: block.timestamp,
            pinDuration: duration,
            fileSize: fileSize,
            amountPaid: msg.value,
            isActive: true,
            encryptedName: encryptedName
        });
        
        // Update mappings
        userPins[msg.sender].push(pinId);
        cidToPinId[fileCID] = pinId;
        
        // Update statistics
        pinnerStats[msg.sender].totalPins++;
        pinnerStats[msg.sender].totalSpent += msg.value;
        pinnerStats[msg.sender].totalSize += fileSize;
        totalPinsCount++;
        totalActiveSize += fileSize;
        
        // Transfer treasury fee
        uint256 treasuryAmount = (msg.value * treasuryFeePercent) / 100;
        if (treasuryAmount > 0) {
            (bool sent, ) = treasury.call{value: treasuryAmount}("");
            require(sent, "Treasury transfer failed");
        }
        
        // Refund excess payment
        if (msg.value > requiredPayment) {
            (bool refunded, ) = msg.sender.call{value: msg.value - requiredPayment}("");
            require(refunded, "Refund failed");
        }
        
        emit FilePinned(pinId, msg.sender, fileCID, metadataCID, duration, msg.value);
    }
    
    /**
     * @notice Extend the duration of an existing pin
     * @param pinId ID of the pin to extend
     * @param additionalDuration Additional duration in seconds
     */
    function extendPin(bytes32 pinId, uint256 additionalDuration) 
        external 
        payable 
        nonReentrant 
        whenNotPaused
        pinExists(pinId)
    {
        PinInfo storage pin = pins[pinId];
        
        // Check if pin is still valid
        require(isPinActive(pinId), "Pin has expired");
        
        // Validate new total duration
        uint256 newTotalDuration = pin.pinDuration + additionalDuration;
        require(newTotalDuration <= maximumPinDuration, "Exceeds maximum duration");
        
        // Calculate required payment
        uint256 requiredPayment = calculatePinCost(pin.fileSize, additionalDuration);
        require(msg.value >= requiredPayment, "Insufficient payment");
        
        // Update pin duration
        pin.pinDuration += additionalDuration;
        pin.amountPaid += msg.value;
        
        // Update statistics
        pinnerStats[msg.sender].totalSpent += msg.value;
        
        // Transfer treasury fee
        uint256 treasuryAmount = (msg.value * treasuryFeePercent) / 100;
        if (treasuryAmount > 0) {
            (bool sent, ) = treasury.call{value: treasuryAmount}("");
            require(sent, "Treasury transfer failed");
        }
        
        // Refund excess payment
        if (msg.value > requiredPayment) {
            (bool refunded, ) = msg.sender.call{value: msg.value - requiredPayment}("");
            require(refunded, "Refund failed");
        }
        
        emit PinExtended(pinId, msg.sender, additionalDuration, msg.value);
    }
    
    /**
     * @notice Check if a pin is still active
     * @param pinId ID of the pin to check
     * @return active Whether the pin is active
     */
    function isPinActive(bytes32 pinId) public view returns (bool) {
        PinInfo memory pin = pins[pinId];
        if (!pin.isActive) return false;
        
        uint256 expiryTime = pin.pinStartTime + pin.pinDuration;
        return block.timestamp < expiryTime;
    }
    
    /**
     * @notice Get pin expiry time
     * @param pinId ID of the pin
     * @return expiryTime Timestamp when pin expires
     */
    function getPinExpiryTime(bytes32 pinId) public view returns (uint256) {
        PinInfo memory pin = pins[pinId];
        return pin.pinStartTime + pin.pinDuration;
    }
    
    /**
     * @notice Get all pins for a user
     * @param user Address of the user
     * @return pinIds Array of pin IDs
     */
    function getUserPins(address user) external view returns (bytes32[] memory) {
        return userPins[user];
    }
    
    /**
     * @notice Get active pins for a user
     * @param user Address of the user
     * @return activePinIds Array of active pin IDs
     */
    function getUserActivePins(address user) external view returns (bytes32[] memory) {
        bytes32[] memory allPins = userPins[user];
        uint256 activeCount = 0;
        
        // Count active pins
        for (uint256 i = 0; i < allPins.length; i++) {
            if (isPinActive(allPins[i])) {
                activeCount++;
            }
        }
        
        // Create array of active pins
        bytes32[] memory activePins = new bytes32[](activeCount);
        uint256 currentIndex = 0;
        
        for (uint256 i = 0; i < allPins.length; i++) {
            if (isPinActive(allPins[i])) {
                activePins[currentIndex] = allPins[i];
                currentIndex++;
            }
        }
        
        return activePins;
    }
    
    /**
     * @notice Batch pin multiple files
     * @param fileCIDs Array of file CIDs
     * @param metadataCIDs Array of metadata CIDs
     * @param fileSizes Array of file sizes
     * @param duration Pin duration for all files
     * @param encryptedNames Array of encrypted file names
     */
    function batchPinFiles(
        string[] memory fileCIDs,
        string[] memory metadataCIDs,
        uint256[] memory fileSizes,
        uint256 duration,
        string[] memory encryptedNames
    ) 
        external 
        payable 
        nonReentrant 
        whenNotPaused
        validDuration(duration)
    {
        require(
            fileCIDs.length == metadataCIDs.length && 
            fileCIDs.length == fileSizes.length &&
            fileCIDs.length == encryptedNames.length,
            "Array lengths mismatch"
        );
        require(fileCIDs.length > 0 && fileCIDs.length <= 50, "Invalid batch size");
        
        uint256 totalCost = 0;
        
        // Calculate total cost
        for (uint256 i = 0; i < fileSizes.length; i++) {
            totalCost += calculatePinCost(fileSizes[i], duration);
        }
        
        require(msg.value >= totalCost, "Insufficient payment for batch");
        
        // Pin each file
        for (uint256 i = 0; i < fileCIDs.length; i++) {
            // Check if CID is already pinned
            if (cidToPinId[fileCIDs[i]] == bytes32(0)) {
                // Generate unique pin ID
                bytes32 pinId = keccak256(
                    abi.encodePacked(fileCIDs[i], msg.sender, block.timestamp, i)
                );
                
                // Calculate individual cost
                uint256 individualCost = calculatePinCost(fileSizes[i], duration);
                
                // Create pin record
                pins[pinId] = PinInfo({
                    fileCID: fileCIDs[i],
                    metadataCID: metadataCIDs[i],
                    pinner: msg.sender,
                    pinStartTime: block.timestamp,
                    pinDuration: duration,
                    fileSize: fileSizes[i],
                    amountPaid: individualCost,
                    isActive: true,
                    encryptedName: encryptedNames[i]
                });
                
                // Update mappings
                userPins[msg.sender].push(pinId);
                cidToPinId[fileCIDs[i]] = pinId;
                
                // Update statistics
                pinnerStats[msg.sender].totalPins++;
                pinnerStats[msg.sender].totalSpent += individualCost;
                pinnerStats[msg.sender].totalSize += fileSizes[i];
                totalPinsCount++;
                totalActiveSize += fileSizes[i];
                
                emit FilePinned(
                    pinId, 
                    msg.sender, 
                    fileCIDs[i], 
                    metadataCIDs[i], 
                    duration, 
                    individualCost
                );
            }
        }
        
        // Transfer treasury fee
        uint256 treasuryAmount = (totalCost * treasuryFeePercent) / 100;
        if (treasuryAmount > 0) {
            (bool sent, ) = treasury.call{value: treasuryAmount}("");
            require(sent, "Treasury transfer failed");
        }
        
        // Refund excess payment
        if (msg.value > totalCost) {
            (bool refunded, ) = msg.sender.call{value: msg.value - totalCost}("");
            require(refunded, "Refund failed");
        }
    }
    
    /**
     * @notice Remove an expired pin (cleanup function)
     * @param pinId ID of the pin to remove
     */
    function removeExpiredPin(bytes32 pinId) external {
        require(pins[pinId].isActive, "Pin not active");
        require(!isPinActive(pinId), "Pin is still active");
        
        PinInfo storage pin = pins[pinId];
        
        // Update state
        pin.isActive = false;
        totalActiveSize -= pin.fileSize;
        delete cidToPinId[pin.fileCID];
        
        emit PinRemoved(pinId, msg.sender);
    }
    
    // Admin functions
    
    /**
     * @notice Update the price per GB per day
     * @param newPrice New price in wei
     */
    function updatePrice(uint256 newPrice) external onlyOwner {
        require(newPrice > 0, "Price must be greater than 0");
        pricePerGBPerDay = newPrice;
        emit PriceUpdated(newPrice);
    }
    
    /**
     * @notice Update treasury address
     * @param newTreasury New treasury address
     */
    function updateTreasury(address newTreasury) external onlyOwner {
        require(newTreasury != address(0), "Invalid treasury address");
        treasury = newTreasury;
        emit TreasuryUpdated(newTreasury);
    }
    
    /**
     * @notice Update treasury fee percentage
     * @param newFeePercent New fee percentage (0-100)
     */
    function updateTreasuryFee(uint256 newFeePercent) external onlyOwner {
        require(newFeePercent <= 100, "Fee too high");
        treasuryFeePercent = newFeePercent;
    }
    
    /**
     * @notice Pause contract
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @notice Unpause contract
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @notice Emergency withdraw (only owner)
     */
    function emergencyWithdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No balance to withdraw");
        
        (bool sent, ) = owner().call{value: balance}("");
        require(sent, "Withdrawal failed");
    }
}