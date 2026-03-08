# Whitelist API Endpoints - Add to main.py after stop_system endpoint

@app.get("/api/whitelist")
async def get_whitelist():
    """Get all whitelist entries"""
    try:
        from core.whitelist_manager import get_whitelist_manager
        whitelist = get_whitelist_manager()
        data = whitelist.get_all()
        stats = whitelist.get_stats()
        
        return {
            "whitelist": data,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/whitelist/add")
async def add_to_whitelist(
    process_name: str,
    description: str = "",
    process_path: str = None
):
    """Add process to whitelist"""
    try:
        from core.whitelist_manager import get_whitelist_manager
        whitelist = get_whitelist_manager()
        
        success = whitelist.add_to_whitelist(
            process_name=process_name,
            description=description,
            process_path=process_path,
            auto_detected=False
        )
        
        if success:
            return {
                "success": True,
                "message": f"Added {process_name} to whitelist"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add to whitelist")
    
    except Exception as e:
        logger.error(f"Failed to add to whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/whitelist/remove")
async def remove_from_whitelist(
    process_name: str = None,
    process_path: str = None
):
    """Remove process from whitelist"""
    try:
        from core.whitelist_manager import get_whitelist_manager
        whitelist = get_whitelist_manager()
        
        success = whitelist.remove_from_whitelist(
            process_name=process_name,
            process_path=process_path
        )
        
        if success:
            return {
                "success": True,
                "message": "Removed from whitelist"
            }
        else:
            raise HTTPException(status_code=404, detail="Entry not found in whitelist")
    
    except Exception as e:
        logger.error(f"Failed to remove from whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/whitelist/clear")
async def clear_whitelist(keep_defaults: bool = True):
    """Clear whitelist"""
    try:
        from core.whitelist_manager import get_whitelist_manager
        whitelist = get_whitelist_manager()
        
        whitelist.clear_whitelist(keep_defaults=keep_defaults)
        
        return {
            "success": True,
            "message": "Whitelist cleared" + (" (defaults kept)" if keep_defaults else "")
        }
    except Exception as e:
        logger.error(f"Failed to clear whitelist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/whitelist/stats")
async def get_whitelist_stats():
    """Get whitelist statistics"""
    try:
        from core.whitelist_manager import get_whitelist_manager
        whitelist = get_whitelist_manager()
        
        return whitelist.get_stats()
    except Exception as e:
        logger.error(f"Failed to get whitelist stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
